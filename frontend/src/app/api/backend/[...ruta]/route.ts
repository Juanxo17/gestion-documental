import { cookies } from "next/headers";
import type { NextRequest } from "next/server";

import { BACKEND_URL, COOKIE_SESION, ESPERA_MAXIMA_MS, errorSinBackend } from "@/lib/servidor";

const CABECERAS_DE_RESPUESTA = ["content-type", "content-disposition", "x-content-sha256"];

async function reenviar(
  request: NextRequest,
  { params }: { params: Promise<{ ruta: string[] }> },
): Promise<Response> {
  const { ruta } = await params;
  if (ruta[0] === "auth" && ruta[1] === "login") {
    return Response.json(
      { error: "NO_ENCONTRADO", detalle: "Usa /api/auth/login para iniciar sesión" },
      { status: 404 },
    );
  }
  const token = (await cookies()).get(COOKIE_SESION)?.value;
  const cabeceras = new Headers();
  const tipo = request.headers.get("content-type");
  if (tipo) cabeceras.set("content-type", tipo);
  if (token) cabeceras.set("authorization", `Bearer ${token}`);

  const destino = `${BACKEND_URL}/${ruta.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;
  const conCuerpo = !["GET", "HEAD"].includes(request.method);
  let respuesta: Response;
  try {
    respuesta = await fetch(destino, {
      method: request.method,
      headers: cabeceras,
      body: conCuerpo ? await request.arrayBuffer() : undefined,
      signal: AbortSignal.timeout(ESPERA_MAXIMA_MS),
      cache: "no-store",
    });
  } catch (causa) {
    return errorSinBackend(destino, causa);
  }
  const salida = new Headers();
  for (const nombre of CABECERAS_DE_RESPUESTA) {
    const valor = respuesta.headers.get(nombre);
    if (valor) salida.set(nombre, valor);
  }
  return new Response(respuesta.body, { status: respuesta.status, headers: salida });
}

export { reenviar as DELETE, reenviar as GET, reenviar as PATCH, reenviar as POST, reenviar as PUT };
