export const BACKEND_URL = (process.env.BACKEND_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
export const COOKIE_SESION = "sesion";
export const ESPERA_MAXIMA_MS = 90_000;
const MINUTOS_SESION = Number(process.env.JWT_MINUTOS ?? 60);

export const OPCIONES_COOKIE = {
  httpOnly: true,
  secure: true,
  sameSite: "lax" as const,
  path: "/",
  maxAge: MINUTOS_SESION * 60,
};

export function errorSinBackend(): Response {
  return Response.json(
    {
      error: "BACKEND_NO_DISPONIBLE",
      detalle: "No fue posible comunicarse con el servidor. Intenta de nuevo en un momento.",
    },
    { status: 502 },
  );
}
