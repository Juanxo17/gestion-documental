export const EVENTO_SERVIDOR_LENTO = "servidor-lento";
const ESPERA_ANTES_DE_AVISAR_MS = 4_000;

const MENSAJES_POR_CODIGO: Record<string, string> = {
  NO_AUTENTICADO: "Tu sesión terminó. Vuelve a iniciar sesión.",
  METODO_NO_PERMITIDO: "La operación no está permitida.",
  BD_NO_DISPONIBLE: "La base de datos no está disponible en este momento.",
};

export class ErrorApi extends Error {
  constructor(
    readonly estado: number,
    readonly codigo: string,
    mensaje: string,
  ) {
    super(mensaje);
  }
}

type CuerpoError = { error?: string; detalle?: string } | null;

function mensajeDe(codigo: string, detalle: string | undefined): string {
  if (codigo === "VALIDACION" && detalle) {
    const campos = detalle
      .split(";")
      .map((parte) => parte.split(":")[0].trim())
      .filter(Boolean);
    return `Revisa estos datos: ${[...new Set(campos)].join(", ")}.`;
  }
  if (codigo === "NO_AUTENTICADO" && detalle === "Not authenticated") {
    return MENSAJES_POR_CODIGO.NO_AUTENTICADO;
  }
  return detalle || MENSAJES_POR_CODIGO[codigo] || "Ocurrió un error inesperado.";
}

function avisarLentitud(lento: boolean) {
  window.dispatchEvent(new CustomEvent(EVENTO_SERVIDOR_LENTO, { detail: lento }));
}

async function solicitar(url: string, opciones: RequestInit): Promise<Response> {
  const temporizador = window.setTimeout(() => avisarLentitud(true), ESPERA_ANTES_DE_AVISAR_MS);
  try {
    return await fetch(url, { ...opciones, cache: "no-store" });
  } finally {
    window.clearTimeout(temporizador);
    avisarLentitud(false);
  }
}

async function interpretar<T>(respuesta: Response): Promise<T> {
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as CuerpoError;
    const codigo = cuerpo?.error ?? "ERROR";
    if (respuesta.status === 401 && window.location.pathname !== "/login") {
      window.location.replace(`${window.location.origin}/login`);
    }
    throw new ErrorApi(respuesta.status, codigo, mensajeDe(codigo, cuerpo?.detalle));
  }
  if (respuesta.status === 204) return undefined as T;
  return (await respuesta.json()) as T;
}

export async function api<T>(ruta: string, opciones: RequestInit = {}): Promise<T> {
  const esFormulario = opciones.body instanceof FormData;
  const respuesta = await solicitar(`/api/backend${ruta}`, {
    ...opciones,
    headers: esFormulario ? opciones.headers : { "content-type": "application/json", ...opciones.headers },
  });
  return interpretar<T>(respuesta);
}

export function enviar<T>(ruta: string, metodo: string, cuerpo?: unknown): Promise<T> {
  return api<T>(ruta, {
    method: metodo,
    body: cuerpo instanceof FormData ? cuerpo : JSON.stringify(cuerpo ?? {}),
  });
}

export async function iniciarSesion(correo: string, contrasena: string): Promise<void> {
  const respuesta = await solicitar("/api/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ correo, contrasena }),
  });
  await interpretar<unknown>(respuesta);
}

export async function cerrarSesion(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST" });
  window.location.replace(`${window.location.origin}/login`);
}

export function mensajeDeError(error: unknown): string {
  return error instanceof Error ? error.message : "Ocurrió un error inesperado.";
}
