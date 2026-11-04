"use client";

import { useEffect, useState } from "react";

import { EVENTO_SERVIDOR_LENTO } from "@/lib/api";

export function AvisoServidor() {
  const [lento, setLento] = useState(false);

  useEffect(() => {
    const escuchar = (evento: Event) => setLento((evento as CustomEvent<boolean>).detail);
    window.addEventListener(EVENTO_SERVIDOR_LENTO, escuchar);
    return () => window.removeEventListener(EVENTO_SERVIDOR_LENTO, escuchar);
  }, []);

  if (!lento) return null;
  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 top-0 z-50 bg-amber-100 px-4 py-2 text-center text-sm font-medium text-amber-950"
    >
      Iniciando el servidor, puede tardar hasta un minuto.
    </div>
  );
}
