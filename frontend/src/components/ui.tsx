import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
} from "react";

import { COLOR_ESTADO, NOMBRE_ESTADO } from "@/lib/formato";

type Variante = "primario" | "secundario" | "peligro";

const ESTILO_BOTON: Record<Variante, string> = {
  primario: "bg-blue-700 text-white hover:bg-blue-800",
  secundario: "border border-slate-300 bg-white text-slate-900 hover:bg-slate-100",
  peligro: "bg-rose-700 text-white hover:bg-rose-800",
};

export function Boton({
  variante = "primario",
  className = "",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variante?: Variante }) {
  return (
    <button
      className={`inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-60 ${ESTILO_BOTON[variante]} ${className}`}
      {...props}
    />
  );
}

export function Campo({
  etiqueta,
  id,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { etiqueta: string; id: string }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-800">
        {etiqueta}
      </label>
      <input
        id={id}
        name={id}
        className="rounded-md border border-slate-400 bg-white px-3 py-2 text-sm text-slate-900"
        {...props}
      />
    </div>
  );
}

export function Selector({
  etiqueta,
  id,
  opciones,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & {
  etiqueta: string;
  id: string;
  opciones: { valor: string; texto: string }[];
}) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-medium text-slate-800">
        {etiqueta}
      </label>
      <select
        id={id}
        name={id}
        className="rounded-md border border-slate-400 bg-white px-3 py-2 text-sm text-slate-900"
        {...props}
      >
        {opciones.map((opcion) => (
          <option key={opcion.valor} value={opcion.valor}>
            {opcion.texto}
          </option>
        ))}
      </select>
    </div>
  );
}

export function Tarjeta({ titulo, children }: { titulo?: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm sm:p-6">
      {titulo && <h2 className="mb-4 text-lg font-semibold text-slate-900">{titulo}</h2>}
      {children}
    </section>
  );
}

export function Alerta({ tipo = "error", children }: { tipo?: "error" | "exito"; children: ReactNode }) {
  if (!children) return null;
  const estilo =
    tipo === "error"
      ? "border-rose-300 bg-rose-50 text-rose-900"
      : "border-emerald-300 bg-emerald-50 text-emerald-900";
  return (
    <p role={tipo === "error" ? "alert" : "status"} className={`rounded-md border px-3 py-2 text-sm ${estilo}`}>
      {children}
    </p>
  );
}

export function Insignia({ estado }: { estado: string }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${COLOR_ESTADO[estado] ?? "bg-slate-100"}`}>
      {NOMBRE_ESTADO[estado as keyof typeof NOMBRE_ESTADO] ?? estado}
    </span>
  );
}

export function Titulo({ children, accion }: { children: ReactNode; accion?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
      <h1 className="text-2xl font-bold text-slate-900">{children}</h1>
      {accion}
    </div>
  );
}

export function Cargando() {
  return (
    <p role="status" className="text-sm text-slate-600">
      Cargando...
    </p>
  );
}
