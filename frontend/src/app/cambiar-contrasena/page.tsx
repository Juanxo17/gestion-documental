"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { AvisoServidor } from "@/components/AvisoServidor";
import { Alerta, Boton, Campo } from "@/components/ui";
import { cerrarSesion, enviar, mensajeDeError } from "@/lib/api";

export default function CambiarContrasena() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function cambiar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = new FormData(evento.currentTarget);
    const nueva = String(formulario.get("nueva"));
    if (nueva !== String(formulario.get("confirmacion"))) {
      setError("La confirmación no coincide con la contraseña nueva.");
      return;
    }
    setEnviando(true);
    setError("");
    try {
      await enviar("/auth/cambiar-contrasena", "POST", {
        contrasena_actual: String(formulario.get("actual")),
        contrasena_nueva: nueva,
      });
      router.replace("/dashboard");
    } catch (causa) {
      setError(mensajeDeError(causa));
      setEnviando(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center px-4">
      <AvisoServidor />
      <form
        onSubmit={cambiar}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Cambia tu contraseña</h1>
          <p className="text-sm text-slate-600">
            Por seguridad debes definir una contraseña nueva antes de continuar.
          </p>
        </div>
        <Campo etiqueta="Contraseña actual" id="actual" type="password" autoComplete="current-password" required />
        <Campo
          etiqueta="Contraseña nueva (mínimo 8 caracteres)"
          id="nueva"
          type="password"
          minLength={8}
          autoComplete="new-password"
          required
        />
        <Campo etiqueta="Confirma la contraseña nueva" id="confirmacion" type="password" autoComplete="new-password" required />
        <Alerta>{error}</Alerta>
        <Boton type="submit" className="w-full" disabled={enviando}>
          Guardar contraseña
        </Boton>
        <Boton type="button" variante="secundario" className="w-full" onClick={cerrarSesion}>
          Salir
        </Boton>
      </form>
    </main>
  );
}
