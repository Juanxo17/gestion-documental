"use client";

import { Alerta, Cargando, Tarjeta, Titulo } from "@/components/ui";
import { NOMBRE_ESTADO, dinero } from "@/lib/formato";
import type { Grupo, Resumen } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

function Barras({ grupos, nombre }: { grupos: Grupo[]; nombre: (clave: string) => string }) {
  const maximo = Math.max(1, ...grupos.map((grupo) => Number(grupo.total)));
  if (grupos.length === 0) return <p className="text-sm text-slate-600">Sin datos todavía.</p>;
  return (
    <ul className="space-y-3">
      {grupos.map((grupo) => (
        <li key={grupo.clave}>
          <div className="flex justify-between text-sm">
            <span className="font-medium text-slate-900">
              {nombre(grupo.clave)} ({grupo.cantidad})
            </span>
            <span className="text-slate-700">{dinero(grupo.total)}</span>
          </div>
          <div className="mt-1 h-3 rounded bg-slate-100" aria-hidden="true">
            <div
              className="h-3 rounded bg-blue-700"
              style={{ width: `${(Number(grupo.total) / maximo) * 100}%` }}
            />
          </div>
        </li>
      ))}
    </ul>
  );
}

export default function Dashboard() {
  const { datos, error } = useDatos<Resumen>("/dashboard/resumen");
  const cantidad = datos?.por_estado.reduce((suma, grupo) => suma + grupo.cantidad, 0) ?? 0;
  const total = datos?.por_estado.reduce((suma, grupo) => suma + Number(grupo.total), 0) ?? 0;

  return (
    <>
      <Titulo>Resumen</Titulo>
      <Alerta>{error}</Alerta>
      {!datos && !error && <Cargando />}
      {datos && (
        <div className="grid gap-6">
          <div className="grid gap-4 sm:grid-cols-2">
            <Tarjeta>
              <p className="text-sm text-slate-600">Cuentas registradas</p>
              <p className="text-3xl font-bold text-slate-900">{cantidad}</p>
            </Tarjeta>
            <Tarjeta>
              <p className="text-sm text-slate-600">Valor total cobrado</p>
              <p className="text-3xl font-bold text-slate-900">{dinero(total)}</p>
            </Tarjeta>
          </div>
          <div className="grid gap-6 lg:grid-cols-2">
            <Tarjeta titulo="Por estado">
              <Barras
                grupos={datos.por_estado}
                nombre={(clave) => NOMBRE_ESTADO[clave as keyof typeof NOMBRE_ESTADO] ?? clave}
              />
            </Tarjeta>
            <Tarjeta titulo="Por contrato">
              <Barras grupos={datos.por_contrato} nombre={(clave) => clave} />
            </Tarjeta>
          </div>
        </div>
      )}
    </>
  );
}
