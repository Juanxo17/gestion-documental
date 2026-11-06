"use client";

import { type FormEvent, useState } from "react";

import { Alerta, Boton, Campo, Cargando, Selector, Tarjeta, Titulo } from "@/components/ui";
import { enviar, mensajeDeError } from "@/lib/api";
import { useSesion } from "@/lib/sesion";
import type { Contratista } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

export default function Contratistas() {
  const { puede } = useSesion();
  const gestiona = puede("contratistas.gestionar");
  const [busqueda, setBusqueda] = useState("");
  const { datos, error, recargar } = useDatos<Contratista[]>(
    `/contratistas?${new URLSearchParams(busqueda ? { q: busqueda } : {})}`,
  );
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

  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setBusqueda(String(new FormData(evento.currentTarget).get("q") ?? "").trim());
  }

  async function crear(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datos = Object.fromEntries(
      [...new FormData(formulario)].map(([clave, valor]) => [clave, String(valor).trim() || null]),
    );
    if (await ejecutar(() => enviar("/contratistas", "POST", datos), "Contratista creado.")) formulario.reset();
  }

  return (
    <>
      <Titulo>Contratistas</Titulo>
      <form onSubmit={buscar} className="mb-4 flex flex-wrap items-end gap-3">
        <Campo etiqueta="Buscar por nombre o identificación" id="q" />
        <Boton type="submit">Buscar</Boton>
      </form>
      <div className="mb-4 space-y-2">
        <Alerta>{error || mensaje.error}</Alerta>
        <Alerta tipo="exito">{mensaje.exito}</Alerta>
      </div>
      {!datos && !error && <Cargando />}
      {datos && (
        <div className="mb-6 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">Listado de contratistas</caption>
            <thead className="bg-slate-100 text-slate-800">
              <tr>
                <th scope="col" className="px-4 py-3">Nombre</th>
                <th scope="col" className="px-4 py-3">Tipo</th>
                <th scope="col" className="px-4 py-3">Identificación</th>
                <th scope="col" className="px-4 py-3">Correo</th>
                <th scope="col" className="px-4 py-3">Estado</th>
                {gestiona && <th scope="col" className="px-4 py-3"><span className="sr-only">Acciones</span></th>}
              </tr>
            </thead>
            <tbody>
              {datos.map((contratista) => (
                <tr key={contratista.id} className="border-t border-slate-200">
                  <td className="px-4 py-3 font-medium">{contratista.nombre_completo}</td>
                  <td className="px-4 py-3">{contratista.tipo_persona === "NATURAL" ? "Persona natural" : "Persona jurídica"}</td>
                  <td className="px-4 py-3">{contratista.nit_cedula}</td>
                  <td className="px-4 py-3">{contratista.correo ?? ""}</td>
                  <td className="px-4 py-3">{contratista.activo ? "Activo" : "Inactivo"}</td>
                  {gestiona && (
                    <td className="px-4 py-3">
                      {contratista.activo ? (
                        <Boton
                          variante="secundario"
                          className="px-2 py-1 text-xs"
                          onClick={() => ejecutar(() => enviar(`/contratistas/${contratista.id}/desactivar`, "POST"), "Contratista desactivado.")}
                        >
                          Desactivar
                        </Boton>
                      ) : (
                        <Boton
                          className="px-2 py-1 text-xs"
                          onClick={() => ejecutar(() => enviar(`/contratistas/${contratista.id}/activar`, "POST"), "Contratista activado.")}
                        >
                          Activar
                        </Boton>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {gestiona && (
        <Tarjeta titulo="Nuevo contratista">
          <form onSubmit={crear} className="grid gap-4 sm:grid-cols-2">
            <Selector
              etiqueta="Tipo de persona"
              id="tipo_persona"
              opciones={[
                { valor: "NATURAL", texto: "Persona natural (cédula)" },
                { valor: "JURIDICA", texto: "Persona jurídica (NIT)" },
              ]}
            />
            <Campo etiqueta="Nombre completo o razón social" id="nombre_completo" required />
            <Campo etiqueta="Cédula o NIT (con o sin dígito: 900000001-2)" id="nit_cedula" required />
            <Campo etiqueta="Teléfono" id="telefono" />
            <Campo etiqueta="Correo" id="correo" type="email" />
            <Campo etiqueta="Dirección" id="direccion" />
            <div className="sm:col-span-2">
              <Boton type="submit">Crear contratista</Boton>
            </div>
          </form>
        </Tarjeta>
      )}
    </>
  );
}
