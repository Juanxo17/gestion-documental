"use client";

import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { AvisoServidor } from "@/components/AvisoServidor";
import { Alerta, Boton, Campo } from "@/components/ui";
import { iniciarSesion, mensajeDeError } from "@/lib/api";

export default function Login() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function entrar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = new FormData(evento.currentTarget);
    setEnviando(true);
    setError("");
    try {
      await iniciarSesion(String(formulario.get("correo")), String(formulario.get("contrasena")));
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
        onSubmit={entrar}
        className="w-full max-w-sm space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm"
      >
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Gestión Documental</h1>
          <p className="text-sm text-slate-600">Cuentas de cobro de contratistas</p>
        </div>
        <Campo etiqueta="Correo" id="correo" type="email" autoComplete="username" required />
        <Campo
          etiqueta="Contraseña"
          id="contrasena"
          type="password"
          autoComplete="current-password"
          required
        />
        <Alerta>{error}</Alerta>
        <Boton type="submit" className="w-full" disabled={enviando}>
          {enviando ? "Ingresando..." : "Ingresar"}
        </Boton>
      </form>
    </main>
  );
}
