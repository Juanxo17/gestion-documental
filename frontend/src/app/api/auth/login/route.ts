import { cookies } from "next/headers";

import {
  BACKEND_URL,
  COOKIE_SESION,
  ESPERA_MAXIMA_MS,
  OPCIONES_COOKIE,
  errorSinBackend,
} from "@/lib/servidor";

export async function POST(request: Request) {
  const { correo, contrasena } = (await request.json()) as {
    correo?: string;
    contrasena?: string;
  };
  let respuesta: Response;
  try {
    respuesta = await fetch(`${BACKEND_URL}/auth/login`, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ username: correo ?? "", password: contrasena ?? "" }),
      signal: AbortSignal.timeout(ESPERA_MAXIMA_MS),
      cache: "no-store",
    });
  } catch (causa) {
    return errorSinBackend(`${BACKEND_URL}/auth/login`, causa);
  }
  const cuerpo = await respuesta.json();
  if (!respuesta.ok) {
    return Response.json(cuerpo, { status: respuesta.status });
  }
  (await cookies()).set(COOKIE_SESION, cuerpo.access_token, OPCIONES_COOKIE);
  return Response.json({ ok: true });
}
