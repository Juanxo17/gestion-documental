"use client";

import { useCallback, useEffect, useState } from "react";

import { api, mensajeDeError } from "./api";

export function useDatos<T>(ruta: string | null) {
  const [datos, setDatos] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [version, setVersion] = useState(0);

  useEffect(() => {
    if (ruta === null) return;
    let vigente = true;
    api<T>(ruta)
      .then((respuesta) => {
        if (vigente) {
          setDatos(respuesta);
          setError("");
        }
      })
      .catch((causa: unknown) => {
        if (vigente) setError(mensajeDeError(causa));
      });
    return () => {
      vigente = false;
    };
  }, [ruta, version]);

  const recargar = useCallback(() => setVersion((actual) => actual + 1), []);
  return { datos, error, recargar };
}
