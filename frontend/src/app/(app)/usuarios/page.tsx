"use client";

import { type FormEvent, useState } from "react";

import { Alerta, Boton, Campo, Cargando, Selector, Tarjeta, Titulo } from "@/components/ui";
import { enviar, mensajeDeError } from "@/lib/api";
import { fechaHora } from "@/lib/formato";
import { useSesion } from "@/lib/sesion";
import { ROLES, type Usuario } from "@/lib/tipos";
import { useDatos } from "@/lib/useDatos";

const OPCIONES_ROL = ROLES.map((rol) => ({ valor: rol, texto: rol }));

export default function Usuarios() {
  const { usuario: actual } = useSesion();
  const { datos, error, recargar } = useDatos<Usuario[]>("/usuarios");
  const [mensaje, setMensaje] = useState({ error: "", exito: "" });

  async function ejecutar(operacion: () => Promise<unknown>, exito: (resultado: unknown) => string) {
    setMensaje({ error: "", exito: "" });
    try {
      const resultado = await operacion();
      setMensaje({ error: "", exito: exito(resultado) });
      recargar();
      return true;
    } catch (causa) {
      setMensaje({ error: mensajeDeError(causa), exito: "" });
      return false;
    }
  }

  async function crear(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const formulario = evento.currentTarget;
    const datosFormulario = Object.fromEntries(new FormData(formulario));
    const creado = await ejecutar(
      () => enviar<{ contrasena_temporal: string }>("/usuarios", "POST", datosFormulario),
      (resultado) =>
        `Usuario creado. Contraseña temporal: ${(resultado as { contrasena_temporal: string }).contrasena_temporal} (compártela por un canal seguro; deberá cambiarla al entrar).`,
    );
    if (creado) formulario.reset();
  }

  return (
    <>
      <Titulo>Usuarios</Titulo>
      <div className="mb-4 space-y-2">
        <Alerta>{error || mensaje.error}</Alerta>
        <Alerta tipo="exito">{mensaje.exito}</Alerta>
      </div>
      {!datos && !error && <Cargando />}
      {datos && (
        <div className="mb-6 overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="min-w-full text-left text-sm">
            <caption className="sr-only">Listado de usuarios</caption>
            <thead className="bg-slate-100 text-slate-800">
              <tr>
                <th scope="col" className="px-4 py-3">Nombre</th>
                <th scope="col" className="px-4 py-3">Correo</th>
                <th scope="col" className="px-4 py-3">Rol</th>
                <th scope="col" className="px-4 py-3">Estado</th>
                <th scope="col" className="px-4 py-3">Último acceso</th>
                <th scope="col" className="px-4 py-3"><span className="sr-only">Acciones</span></th>
              </tr>
            </thead>
            <tbody>
              {datos.map((usuario) => {
                const bloqueado = usuario.bloqueado_hasta !== null && new Date(usuario.bloqueado_hasta) > new Date();
                return (
                  <tr key={usuario.id} className="border-t border-slate-200 align-top">
                    <td className="px-4 py-3 font-medium">{usuario.nombre} {usuario.apellido}</td>
                    <td className="px-4 py-3">{usuario.correo}</td>
                    <td className="px-4 py-3">
                      <label htmlFor={`rol-${usuario.id}`} className="sr-only">Rol de {usuario.correo}</label>
                      <select
                        id={`rol-${usuario.id}`}
                        value={usuario.rol}
                        disabled={usuario.id === actual.id}
                        className="rounded-md border border-slate-400 bg-white px-2 py-1"
                        onChange={(evento) =>
                          ejecutar(() => enviar(`/usuarios/${usuario.id}/rol`, "PUT", { rol: evento.target.value }), () => "Rol actualizado.")
                        }
                      >
                        {ROLES.map((rol) => <option key={rol} value={rol}>{rol}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      {!usuario.activo ? "Inactivo" : bloqueado ? "Bloqueado" : usuario.debe_cambiar_contrasena ? "Debe cambiar contraseña" : "Activo"}
                    </td>
                    <td className="px-4 py-3">{usuario.ultimo_acceso ? fechaHora(usuario.ultimo_acceso) : "Nunca"}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {usuario.intentos_fallidos > 0 && (
                          <Boton variante="secundario" className="px-2 py-1 text-xs" onClick={() => ejecutar(() => enviar(`/usuarios/${usuario.id}/reiniciar-bloqueo`, "POST"), () => "Bloqueo reiniciado.")}>
                            Reiniciar bloqueo
                          </Boton>
                        )}
                        {usuario.activo && usuario.id !== actual.id && (
                          <Boton variante="peligro" className="px-2 py-1 text-xs" onClick={() => ejecutar(() => enviar(`/usuarios/${usuario.id}/desactivar`, "POST"), () => "Usuario desactivado.")}>
                            Desactivar
                          </Boton>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
      <Tarjeta titulo="Nuevo usuario">
        <form onSubmit={crear} className="grid gap-4 sm:grid-cols-2">
          <Campo etiqueta="Nombre" id="nombre" required />
          <Campo etiqueta="Apellido" id="apellido" required />
          <Campo etiqueta="Correo" id="correo" type="email" required />
          <Campo etiqueta="Cargo" id="cargo" required />
          <Selector etiqueta="Rol" id="rol" opciones={OPCIONES_ROL} />
          <div className="flex items-end">
            <Boton type="submit">Crear usuario</Boton>
          </div>
        </form>
      </Tarjeta>
    </>
  );
}
