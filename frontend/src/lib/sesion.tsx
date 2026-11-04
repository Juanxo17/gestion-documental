"use client";

import { createContext, useContext } from "react";

import type { UsuarioActual } from "./tipos";

export const ContextoSesion = createContext<UsuarioActual | null>(null);

export function useSesion() {
  const usuario = useContext(ContextoSesion);
  if (!usuario) throw new Error("useSesion requiere una sesión cargada");
  return {
    usuario,
    puede: (permiso: string) => usuario.permisos.includes(permiso),
    esAdministrador: usuario.rol === "Administrador",
  };
}
