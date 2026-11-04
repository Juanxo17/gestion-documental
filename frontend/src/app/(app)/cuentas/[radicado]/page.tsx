"use client";

import { useParams } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Alerta, Boton, Campo, Cargando, Insignia, Selector, Tarjeta, Titulo } from "@/components/ui";
import { enviar, mensajeDeError } from "@/lib/api";
import { NOMBRE_ESTADO, dinero, fecha, fechaHora, tamano } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import { type Cuenta, type EstadoCuenta, TIPOS_DOCUMENTO } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

type Accion = { etiqueta: string; ruta: string; cuerpo?: object; permiso: string; peligro?: boolean };

function acciones(estado: EstadoCuenta): Accion[] {
  const cambio = (nuevo: EstadoCuenta, etiqueta: string, peligro = false): Accion => ({
    etiqueta,
    ruta: "estado",
    cuerpo: { nuevo_estado: nuevo },
    permiso: "cuentas.cambiar_estado",
    peligro,
  });
  const anular: Accion = { etiqueta: "Anular", ruta: "anular", permiso: "cuentas.cambiar_estado", peligro: true };
  switch (estado) {
    case "RECIBIDA":
      return [cambio("EN_REVISION", "Enviar a revisión"), anular];
    case "EN_REVISION":
      return [cambio("APROBADA", "Aprobar"), cambio("RECHAZADA", "Rechazar", true), anular];
    case "APROBADA":
      return [{ etiqueta: "Registrar pago", ruta: "pagar", permiso: "cuentas.pagar" }, anular];
    default:
      return [];
  }
}

const OPCIONES_TIPO = TIPOS_DOCUMENTO.map((tipo) => ({ valor: tipo, texto: tipo.replace("_", " ") }));

export default function DetalleCuenta() {
  const { radicado } = useParams<{ radicado: string }>();
  const base = `/cuentas/${encodeURIComponent(decodeURIComponent(radicado))}`;
  const { puede } = useSesion();
  const { datos: cuenta, error, recargar } = useDatos<Cuenta>(base);
  const [mensaje, setMensaje] = useState({ error: "", exito: "" });
  const [ocupado, setOcupado] = useState(false);

  async function ejecutar(operacion: () => Promise<unknown>, exito: string) {
    setOcupado(true);
    setMensaje({ error: "", exito: "" });
    try {
      await operacion();
      setMensaje({ error: "", exito });
      recargar();
    } catch (causa) {
      setMensaje({ error: mensajeDeError(causa), exito: "" });
    } finally {
      setOcupado(false);
    }
  }

  function subirArchivo(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datos = new FormData(formulario);
    ejecutar(() => enviar(`${base}/documentos`, "POST", datos), "Documento adjuntado.").then(() => formulario.reset());
  }

  function adjuntarUrl(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datos = Object.fromEntries(new FormData(formulario));
    ejecutar(() => enviar(`${base}/documentos/url`, "POST", datos), "Enlace adjuntado.").then(() => formulario.reset());
  }

  if (error) return <Alerta>{error}</Alerta>;
  if (!cuenta) return <Cargando />;
  const disponibles = acciones(cuenta.estado).filter((accion) => puede(accion.permiso));
  const editable = cuenta.estado === "RECIBIDA" || cuenta.estado === "EN_REVISION";

  return (
    <>
      <Titulo accion={<Insignia estado={cuenta.estado} />}>Cuenta {cuenta.numero_radicado}</Titulo>
      <div className="space-y-3">
        <Alerta>{mensaje.error}</Alerta>
        <Alerta tipo="exito">{mensaje.exito}</Alerta>
      </div>
      <div className="mt-4 grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Tarjeta titulo="Datos de la cuenta">
            <dl className="grid gap-3 text-sm sm:grid-cols-2">
              <div><dt className="text-slate-600">Número de cuenta</dt><dd className="font-medium">{cuenta.numero_cuenta}</dd></div>
              <div><dt className="text-slate-600">Valor</dt><dd className="font-medium">{dinero(cuenta.valor_cobro)}</dd></div>
              <div><dt className="text-slate-600">Fecha de presentación</dt><dd className="font-medium">{fecha(cuenta.fecha_presentacion)}</dd></div>
              <div><dt className="text-slate-600">Concepto</dt><dd className="font-medium">{cuenta.concepto_pago}</dd></div>
              {cuenta.observaciones && (
                <div className="sm:col-span-2"><dt className="text-slate-600">Observaciones</dt><dd>{cuenta.observaciones}</dd></div>
              )}
            </dl>
            {disponibles.length > 0 && (
              <div className="mt-6 flex flex-wrap gap-2 border-t border-slate-200 pt-4">
                {disponibles.map((accion) => (
                  <Boton
                    key={accion.etiqueta}
                    variante={accion.peligro ? "peligro" : "primario"}
                    disabled={ocupado}
                    onClick={() => ejecutar(() => enviar(`${base}/${accion.ruta}`, "POST", accion.cuerpo), `${accion.etiqueta}: listo.`)}
                  >
                    {accion.etiqueta}
                  </Boton>
                ))}
              </div>
            )}
          </Tarjeta>

          <Tarjeta titulo="Documentos">
            {cuenta.documentos.length === 0 && <p className="text-sm text-slate-600">Sin documentos adjuntos.</p>}
            <ul className="divide-y divide-slate-200">
              {cuenta.documentos.map((documento) => (
                <li key={documento.id_documento} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
                  <div>
                    <p className="font-medium text-slate-900">{documento.nombre_original}</p>
                    <p className="text-slate-600">
                      {documento.tipo.replace("_", " ")} · {documento.origen === "URL" ? "Enlace" : `${documento.tipo_mime} · ${tamano(documento.tamano_bytes)}`}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    {documento.origen === "URL" ? (
                      <a href={documento.ruta_archivo} target="_blank" rel="noreferrer" className="rounded-md border border-slate-300 px-3 py-1.5 text-blue-800 underline">
                        Abrir enlace
                      </a>
                    ) : (
                      puede("documentos.consultar") && (
                        <a href={`/api/backend${base}/documentos/${documento.id_documento}/descarga`} className="rounded-md border border-slate-300 px-3 py-1.5 text-blue-800 underline">
                          Descargar
                        </a>
                      )
                    )}
                    {puede("documentos.eliminar") && editable && (
                      <Boton
                        variante="peligro"
                        disabled={ocupado}
                        aria-label={`Eliminar ${documento.nombre_original}`}
                        onClick={() => ejecutar(() => enviar(`${base}/documentos/${documento.id_documento}`, "DELETE"), "Documento eliminado.")}
                      >
                        Eliminar
                      </Boton>
                    )}
                  </div>
                </li>
              ))}
            </ul>
            {puede("documentos.adjuntar") && !["PAGADA", "RECHAZADA", "ANULADA"].includes(cuenta.estado) && (
              <div className="mt-4 grid gap-6 border-t border-slate-200 pt-4 md:grid-cols-2">
                <form onSubmit={subirArchivo} className="space-y-3">
                  <h3 className="font-semibold text-slate-900">Subir archivo (PDF, JPG o PNG, máx. 10 MB)</h3>
                  <div className="flex flex-col gap-1">
                    <label htmlFor="archivo" className="text-sm font-medium text-slate-800">Archivo</label>
                    <input id="archivo" name="archivo" type="file" accept=".pdf,.jpg,.jpeg,.png" required className="text-sm" />
                  </div>
                  <Selector etiqueta="Tipo de documento" id="tipo" opciones={OPCIONES_TIPO} />
                  <Boton type="submit" disabled={ocupado}>Subir</Boton>
                </form>
                <form onSubmit={adjuntarUrl} className="space-y-3">
                  <h3 className="font-semibold text-slate-900">Adjuntar enlace</h3>
                  <Campo etiqueta="Nombre" id="nombre_original" required />
                  <Campo etiqueta="URL (http o https)" id="url" type="url" required />
                  <Selector etiqueta="Tipo de documento" id="tipo-url" name="tipo" opciones={OPCIONES_TIPO} />
                  <Boton type="submit" disabled={ocupado}>Adjuntar</Boton>
                </form>
              </div>
            )}
          </Tarjeta>
        </div>

        <Tarjeta titulo="Historial">
          <ol className="relative border-l-2 border-slate-300 pl-5">
            {cuenta.historial.map((cambio, indice) => (
              <li key={`${cambio.fecha_cambio}-${indice}`} className="mb-6 last:mb-0">
                <span className="absolute -left-[9px] mt-1 h-4 w-4 rounded-full border-2 border-white bg-blue-700" aria-hidden="true" />
                <p className="font-semibold text-slate-900">{NOMBRE_ESTADO[cambio.estado_nuevo]}</p>
                <p className="text-xs text-slate-600">{fechaHora(cambio.fecha_cambio)}</p>
                {cambio.observacion && <p className="mt-1 text-sm text-slate-800">{cambio.observacion}</p>}
              </li>
            ))}
          </ol>
        </Tarjeta>
      </div>
    </>
  );
}
