"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { Alerta, Boton, Campo, Selector, Tarjeta, Titulo } from "@/components/ui";
import { enviar, mensajeDeError } from "@/lib/api";
import type { Contrato, Cuenta } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

export default function NuevaCuenta() {
  const router = useRouter();
  const { datos: contratos } = useDatos<Contrato[]>("/contratos?estado=ACTIVO");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function radicar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const datos = Object.fromEntries(new FormData(evento.currentTarget)) as Record<string, string>;
    setEnviando(true);
    setError("");
    try {
      const cuenta = await enviar<Cuenta>("/cuentas", "POST", {
        ...datos,
        observaciones: datos.observaciones || null,
      });
      router.push(`/cuentas/${encodeURIComponent(cuenta.numero_radicado)}`);
    } catch (causa) {
      setError(mensajeDeError(causa));
      setEnviando(false);
    }
  }

  return (
    <>
      <Titulo>Radicar cuenta de cobro</Titulo>
      <Tarjeta>
        <form onSubmit={radicar} className="grid gap-4 sm:grid-cols-2">
          <Selector
            etiqueta="Contrato (solo activos)"
            id="numero_contrato"
            required
            opciones={(contratos ?? []).map((c) => ({
              valor: c.numero_contrato,
              texto: `${c.numero_contrato} (${c.fecha_inicio} a ${c.fecha_fin})`,
            }))}
          />
          <Campo etiqueta="Número de radicado" id="numero_radicado" required maxLength={30} />
          <Campo etiqueta="Número de cuenta" id="numero_cuenta" required maxLength={30} />
          <Campo etiqueta="Valor a cobrar" id="valor_cobro" type="number" min="0.01" step="0.01" required />
          <Campo etiqueta="Fecha de presentación" id="fecha_presentacion" type="date" required />
          <Campo etiqueta="Concepto de pago" id="concepto_pago" required />
          <div className="sm:col-span-2">
            <Campo etiqueta="Observaciones (opcional)" id="observaciones" />
          </div>
          <div className="sm:col-span-2 space-y-3">
            <Alerta>{error}</Alerta>
            <Boton type="submit" disabled={enviando}>
              {enviando ? "Radicando..." : "Radicar"}
            </Boton>
          </div>
        </form>
      </Tarjeta>
    </>
  );
}
