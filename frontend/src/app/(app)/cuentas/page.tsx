"use client";

import Link from "next/link";
import { type FormEvent, useState } from "react";

import { Alerta, Boton, Campo, Cargando, Insignia, Selector, Titulo } from "@/components/ui";
import { NOMBRE_ESTADO, dinero, fecha } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import type { PaginaCuentas } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const ESTADOS = ["RECIBIDA", "EN_REVISION", "APROBADA", "RECHAZADA", "PAGADA", "ANULADA"] as const;
const TAMANO_PAGINA = 10;

export default function Cuentas() {
  const { puede } = useSesion();
  const [filtros, setFiltros] = useState<Record<string, string>>({});
  const [pagina, setPagina] = useState(1);
  const parametros = new URLSearchParams({ ...filtros, pagina: String(pagina), tamano: String(TAMANO_PAGINA) });
  const { datos, error } = useDatos<PaginaCuentas>(`/cuentas?${parametros}`);
  const paginas = datos ? Math.max(1, Math.ceil(datos.total / TAMANO_PAGINA)) : 1;

  function filtrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = new FormData(evento.currentTarget);
    const valores: Record<string, string> = {};
    for (const [clave, valor] of formulario.entries()) {
      if (String(valor).trim()) valores[clave] = String(valor).trim();
    }
    setFiltros(valores);
    setPagina(1);
  }

  return (
    <>
      <Titulo
        accion={
          puede("cuentas.radicar") && (
            <Link href="/cuentas/nueva" className="rounded-md bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-800">
              Radicar cuenta
            </Link>
          )
        }
      >
        Cuentas de cobro
      </Titulo>
      <form onSubmit={filtrar} className="mb-6 grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-3 lg:grid-cols-6">
        <Selector
          etiqueta="Estado"
          id="estado"
          opciones={[{ valor: "", texto: "Todos" }, ...ESTADOS.map((e) => ({ valor: e, texto: NOMBRE_ESTADO[e] }))]}
        />
        <Campo etiqueta="Contrato" id="numero_contrato" placeholder="CONT-2025-001" />
        <Campo etiqueta="NIT o cédula" id="nit_contratista" />
        <Campo etiqueta="Desde" id="desde" type="date" />
        <Campo etiqueta="Hasta" id="hasta" type="date" />
        <div className="flex items-end">
          <Boton type="submit" className="w-full">
            Filtrar
          </Boton>
        </div>
      </form>
      <Alerta>{error}</Alerta>
      {!datos && !error && <Cargando />}
      {datos && (
        <>
          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <caption className="sr-only">Listado de cuentas de cobro</caption>
              <thead className="bg-slate-100 text-slate-800">
                <tr>
                  <th scope="col" className="px-4 py-3">Radicado</th>
                  <th scope="col" className="px-4 py-3">Cuenta</th>
                  <th scope="col" className="px-4 py-3">Presentación</th>
                  <th scope="col" className="px-4 py-3">Valor</th>
                  <th scope="col" className="px-4 py-3">Estado</th>
                </tr>
              </thead>
              <tbody>
                {datos.items.map((cuenta) => (
                  <tr key={cuenta.numero_radicado} className="border-t border-slate-200">
                    <td className="px-4 py-3">
                      <Link href={`/cuentas/${encodeURIComponent(cuenta.numero_radicado)}`} className="font-medium text-blue-800 underline">
                        {cuenta.numero_radicado}
                      </Link>
                    </td>
                    <td className="px-4 py-3">{cuenta.numero_cuenta}</td>
                    <td className="px-4 py-3">{fecha(cuenta.fecha_presentacion)}</td>
                    <td className="px-4 py-3">{dinero(cuenta.valor_cobro)}</td>
                    <td className="px-4 py-3">
                      <Insignia estado={cuenta.estado} />
                    </td>
                  </tr>
                ))}
                {datos.items.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-6 text-center text-slate-600">
                      No hay cuentas con esos filtros.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <nav aria-label="Paginación" className="mt-4 flex items-center justify-between text-sm">
            <span className="text-slate-700">
              {datos.total} cuentas. Página {pagina} de {paginas}
            </span>
            <div className="flex gap-2">
              <Boton variante="secundario" disabled={pagina <= 1} onClick={() => setPagina(pagina - 1)}>
                Anterior
              </Boton>
              <Boton variante="secundario" disabled={pagina >= paginas} onClick={() => setPagina(pagina + 1)}>
                Siguiente
              </Boton>
            </div>
          </nav>
        </>
      )}
    </>
  );
}
