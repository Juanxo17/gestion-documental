"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

import { AvisoServidor } from "@/components/AvisoServidor";
import { Alerta, Boton, Cargando } from "@/components/ui";
import { api, cerrarSesion, mensajeDeError } from "@/lib/api";
import { ContextoSesion } from "@/lib/sesion";
import type { UsuarioActual } from "@/lib/tipos";

const MENU = [
  { href: "/dashboard", etiqueta: "Resumen", visible: (u: UsuarioActual) => u.permisos.includes("cuentas.consultar") },
  { href: "/cuentas", etiqueta: "Cuentas de cobro", visible: (u: UsuarioActual) => u.permisos.includes("cuentas.consultar") },
  { href: "/contratos", etiqueta: "Contratos", visible: (u: UsuarioActual) => u.permisos.includes("contratos.consultar") },
  { href: "/contratistas", etiqueta: "Contratistas", visible: (u: UsuarioActual) => u.permisos.includes("contratistas.consultar") },
  { href: "/usuarios", etiqueta: "Usuarios", visible: (u: UsuarioActual) => u.permisos.includes("usuarios.gestionar") },
  { href: "/auditoria", etiqueta: "Auditoría", visible: (u: UsuarioActual) => u.rol === "Administrador" },
];

export default function LayoutPrivado({ children }: { children: ReactNode }) {
  const router = useRouter();
  const ruta = usePathname();
  const [usuario, setUsuario] = useState<UsuarioActual | null>(null);
  const [error, setError] = useState("");
  const [menuAbierto, setMenuAbierto] = useState(false);

  useEffect(() => {
    api<UsuarioActual>("/auth/me")
      .then((actual) => {
        if (actual.debe_cambiar_contrasena) router.replace("/cambiar-contrasena");
        else setUsuario(actual);
      })
      .catch((causa: unknown) => setError(mensajeDeError(causa)));
  }, [router]);

  if (!usuario) {
    return (
      <main className="p-6">
        <AvisoServidor />
        {error ? <Alerta>{error}</Alerta> : <Cargando />}
      </main>
    );
  }

  const enlaces = MENU.filter((opcion) => opcion.visible(usuario));
  return (
    <ContextoSesion.Provider value={usuario}>
      <AvisoServidor />
      <a href="#contenido" className="sr-only focus:not-sr-only focus:absolute focus:left-2 focus:top-2 focus:bg-white focus:p-2">
        Saltar al contenido
      </a>
      <div className="min-h-screen md:flex">
        <header className="border-b border-slate-200 bg-slate-900 text-white md:w-64 md:border-b-0 md:border-r">
          <div className="flex items-center justify-between p-4">
            <span className="font-bold">Gestión Documental</span>
            <button
              type="button"
              className="rounded-md border border-slate-600 px-3 py-1 text-sm md:hidden"
              aria-expanded={menuAbierto}
              aria-controls="menu-principal"
              onClick={() => setMenuAbierto(!menuAbierto)}
            >
              Menú
            </button>
          </div>
          <nav id="menu-principal" aria-label="Menú principal" className={`${menuAbierto ? "block" : "hidden"} md:block`}>
            <ul className="space-y-1 px-2 pb-4">
              {enlaces.map((opcion) => (
                <li key={opcion.href}>
                  <Link
                    href={opcion.href}
                    onClick={() => setMenuAbierto(false)}
                    aria-current={ruta.startsWith(opcion.href) ? "page" : undefined}
                    className={`block rounded-md px-3 py-2 text-sm ${ruta.startsWith(opcion.href) ? "bg-slate-700 font-semibold" : "hover:bg-slate-800"}`}
                  >
                    {opcion.etiqueta}
                  </Link>
                </li>
              ))}
            </ul>
            <div className="border-t border-slate-700 px-4 py-4 text-sm">
              <p className="font-medium">
                {usuario.nombre} {usuario.apellido}
              </p>
              <p className="text-slate-300">{usuario.rol}</p>
              <Boton variante="secundario" className="mt-3 w-full" onClick={cerrarSesion}>
                Cerrar sesión
              </Boton>
            </div>
          </nav>
        </header>
        <main id="contenido" className="flex-1 p-4 sm:p-8">
          {children}
        </main>
      </div>
    </ContextoSesion.Provider>
  );
}
