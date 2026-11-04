"use client";

import { type FormEvent, useState } from "react";

import { Alerta, Boton, Campo, Cargando, Insignia, Selector, Tarjeta, Titulo } from "@/components/ui";
import { enviar, mensajeDeError } from "@/lib/api";
import { NOMBRE_ESTADO, dinero, fecha } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { Contrato, EstadoContrato, Supervisor } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const SIGUIENTES: Record<EstadoContrato, EstadoContrato[]> = {
  ACTIVO: ["SUSPENDIDO", "TERMINADO", "CANCELADO"],
  SUSPENDIDO: ["ACTIVO", "CANCELADO"],
  TERMINADO: ["LIQUIDADO"],
  LIQUIDADO: [],
  CANCELADO: [],
};

export default function Contratos() {
  const { puede } = useSesion();
  const gestiona = puede("contratos.gestionar");
  const { datos: contratos, error, recargar } = useDatos<Contrato[]>("/contratos");
  const { datos: supervisores } = useDatos<Supervisor[]>(gestiona ? "/contratos/supervisores" : null);
  const [mensaje, setMensaje] = useState({ error: "", exito: "" });

  async function ejecutar(operacion: () => Promise<unknown>, exito: string) {
    setMensaje({ error: "", exito: "" });
    try {
      await operacion();
      setMensaje({ error: "", exito });
      recargar();
      return true;
    } catch (causa) {
      setMensaje({ error: mensajeDeError(causa), exito: "" });
      return false;
    }
  }

  async function crear(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datos = Object.fromEntries(new FormData(formulario));
    if (await ejecutar(() => enviar("/contratos", "POST", datos), "Contrato creado.")) formulario.reset();
  }

  return (
    <>
      <Titulo>Contratos</Titulo>
      <div className="mb-4 space-y-2">
        <Alerta>{error || mensaje.error}</Alerta>
        <Alerta tipo="exito">{mensaje.exito}</Alerta>
      </div>
      {!contratos && !error && <Cargando />}
      {contratos && (
        <div className="mb-6 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">Listado de contratos</caption>
            <thead className="bg-slate-100 text-slate-800">
              <tr>
                <th scope="col" className="px-4 py-3">Número</th>
                <th scope="col" className="px-4 py-3">Objeto</th>
                <th scope="col" className="px-4 py-3">Valor</th>
                <th scope="col" className="px-4 py-3">Vigencia</th>
                <th scope="col" className="px-4 py-3">Estado</th>
                {gestiona && <th scope="col" className="px-4 py-3">Cambiar estado</th>}
              </tr>
            </thead>
            <tbody>
              {contratos.map((contrato) => (
                <tr key={contrato.id} className="border-t border-slate-200 align-top">
                  <td className="px-4 py-3 font-medium">{contrato.numero_contrato}</td>
                  <td className="px-4 py-3">{contrato.objeto_contrato}</td>
                  <td className="px-4 py-3">{dinero(contrato.valor_total)}</td>
                  <td className="px-4 py-3">{fecha(contrato.fecha_inicio)} a {fecha(contrato.fecha_fin)}</td>
                  <td className="px-4 py-3"><Insignia estado={contrato.estado} /></td>
                  {gestiona && (
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {SIGUIENTES[contrato.estado].map((estado) => (
                          <Boton
                            key={estado}
                            variante="secundario"
                            className="px-2 py-1 text-xs"
                            onClick={() =>
                              ejecutar(
                                () => enviar(`/contratos/${encodeURIComponent(contrato.numero_contrato)}/estado`, "POST", { nuevo_estado: estado }),
                                `Contrato ${contrato.numero_contrato}: ${NOMBRE_ESTADO[estado]}.`,
                              )
                            }
                          >
                            {NOMBRE_ESTADO[estado]}
                          </Boton>
                        ))}
                      </div>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {gestiona && (
        <Tarjeta titulo="Nuevo contrato">
          <form onSubmit={crear} className="grid gap-4 sm:grid-cols-2">
            <Campo etiqueta="Número de contrato" id="numero_contrato" required />
            <Campo etiqueta="NIT o cédula del contratista" id="nit_contratista" required />
            <div className="sm:col-span-2">
              <Campo etiqueta="Objeto del contrato" id="objeto_contrato" required />
            </div>
            <Campo etiqueta="Valor total" id="valor_total" type="number" min="0.01" step="0.01" required />
            <Selector
              etiqueta="Supervisor"
              id="id_supervisor"
              required
              opciones={(supervisores ?? []).map((s) => ({ valor: s.id, texto: s.nombre_completo }))}
            />
            <Campo etiqueta="Fecha de inicio" id="fecha_inicio" type="date" required />
            <Campo etiqueta="Fecha de fin" id="fecha_fin" type="date" required />
            <div className="sm:col-span-2">
              <Boton type="submit">Crear contrato</Boton>
            </div>
          </form>
        </Tarjeta>
      )}
    </>
  );
}
