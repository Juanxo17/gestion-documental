import type { EstadoContrato, EstadoCuenta } from "./tipos";

const MONEDA = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 2,
});
const FECHA = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeZone: "UTC" });
const FECHA_HORA = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });

export const dinero = (valor: string | number) => MONEDA.format(Number(valor));
export const fecha = (valor: string) => FECHA.format(new Date(valor));
export const fechaHora = (valor: string) => FECHA_HORA.format(new Date(valor));

export const NOMBRE_ESTADO: Record<EstadoCuenta | EstadoContrato, string> = {
  RECIBIDA: "Recibida",
  EN_REVISION: "En revisión",
  APROBADA: "Aprobada",
  RECHAZADA: "Rechazada",
  PAGADA: "Pagada",
  ANULADA: "Anulada",
  ACTIVO: "Activo",
  SUSPENDIDO: "Suspendido",
  LIQUIDADO: "Liquidado",
  TERMINADO: "Terminado",
  CANCELADO: "Cancelado",
};

export const COLOR_ESTADO: Record<string, string> = {
  RECIBIDA: "bg-sky-100 text-sky-900",
  EN_REVISION: "bg-amber-100 text-amber-900",
  APROBADA: "bg-emerald-100 text-emerald-900",
  RECHAZADA: "bg-rose-100 text-rose-900",
  PAGADA: "bg-violet-100 text-violet-900",
  ANULADA: "bg-slate-200 text-slate-800",
  ACTIVO: "bg-emerald-100 text-emerald-900",
  SUSPENDIDO: "bg-amber-100 text-amber-900",
  LIQUIDADO: "bg-violet-100 text-violet-900",
  TERMINADO: "bg-slate-200 text-slate-800",
  CANCELADO: "bg-rose-100 text-rose-900",
};

export function tamano(bytes: number | null): string {
  if (bytes === null) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}
