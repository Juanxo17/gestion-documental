"use client";

import { type FormEvent, useState } from "react";

import { Alerta, Boton, Cargando, Selector, Titulo } from "@/components/ui";
import { fechaHora } from "@/lib/formato";
import type { Evento } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const TIPOS = [
  "CuentaRadicada",
  "EstadoCuentaCambiado",
  "CuentaPagada",
  "CuentaAnulada",
  "CuentaEditada",
  "DocumentoAdjuntado",
  "DocumentoEliminado",
  "ContratoCambiado",
];

export default function Auditoria() {
  const [tipo, setTipo] = useState("");
  const { datos, error } = useDatos<Evento[]>(`/auditoria?${new URLSearchParams(tipo ? { tipo } : {})}`);

  function filtrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    setTipo(String(new FormData(evento.currentTarget).get("tipo") ?? ""));
  }

  return (
    <>
      <Titulo>Auditoría</Titulo>
      <form onSubmit={filtrar} className="mb-4 flex flex-wrap items-end gap-3">
        <Selector
          etiqueta="Tipo de evento"
          id="tipo"
          opciones={[{ valor: "", texto: "Todos" }, ...TIPOS.map((t) => ({ valor: t, texto: t }))]}
        />
        <Boton type="submit">Filtrar</Boton>
      </form>
      <Alerta>{error}</Alerta>
      {!datos && !error && <Cargando />}
      {datos && (
        <ol className="space-y-2">
          {datos.length === 0 && <li className="text-sm text-slate-600">No hay eventos registrados.</li>}
          {datos.map((evento) => (
            <li key={evento.id_evento} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
              <div className="flex flex-wrap justify-between gap-2">
                <span className="font-semibold text-slate-900">{evento.tipo}</span>
                <time dateTime={evento.ocurrido_en} className="text-slate-600">{fechaHora(evento.ocurrido_en)}</time>
              </div>
              <p className="mt-1 text-slate-800">{evento.descripcion}</p>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
