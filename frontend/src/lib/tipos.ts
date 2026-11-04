export type EstadoCuenta =
  | "RECIBIDA"
  | "EN_REVISION"
  | "APROBADA"
  | "RECHAZADA"
  | "PAGADA"
  | "ANULADA";

export type EstadoContrato = "ACTIVO" | "SUSPENDIDO" | "LIQUIDADO" | "TERMINADO" | "CANCELADO";

export const TIPOS_DOCUMENTO = ["CUENTA_COBRO", "CERTIFICADO", "RUT", "CEDULA", "POLIZA", "OTRO"] as const;
export type TipoDocumento = (typeof TIPOS_DOCUMENTO)[number];

export const ROLES = ["Administrador", "Radicador", "Revisor", "Supervisor", "Consulta"] as const;

export type UsuarioActual = {
  id: string;
  nombre: string;
  apellido: string;
  correo: string;
  cargo: string;
  rol: string;
  permisos: string[];
  debe_cambiar_contrasena: boolean;
};

export type Documento = {
  id_documento: string;
  nombre_original: string;
  ruta_archivo: string;
  tipo: TipoDocumento;
  origen: "LOCAL" | "URL";
  tipo_mime: string | null;
  tamano_bytes: number | null;
  hash_sha256: string | null;
  descripcion: string;
};

export type CambioEstado = {
  estado_anterior: EstadoCuenta | null;
  estado_nuevo: EstadoCuenta;
  id_usuario: string;
  fecha_cambio: string;
  observacion: string | null;
};

export type Cuenta = {
  numero_radicado: string;
  numero_cuenta: string;
  id_contrato: string;
  valor_cobro: string;
  concepto_pago: string;
  fecha_presentacion: string;
  estado: EstadoCuenta;
  observaciones: string | null;
  documentos: Documento[];
  historial: CambioEstado[];
};

export type PaginaCuentas = { total: number; pagina: number; tamano: number; items: Cuenta[] };

export type Contrato = {
  id: string;
  numero_contrato: string;
  id_contratista: string;
  objeto_contrato: string;
  valor_total: string;
  fecha_inicio: string;
  fecha_fin: string;
  estado: EstadoContrato;
  id_supervisor: string;
};

export type Contratista = {
  id: string;
  tipo_persona: "NATURAL" | "JURIDICA";
  nombre_completo: string;
  nit_cedula: string;
  telefono: string | null;
  correo: string | null;
  direccion: string | null;
  activo: boolean;
};

export type Usuario = {
  id: string;
  nombre: string;
  apellido: string;
  correo: string;
  cargo: string;
  rol: string;
  activo: boolean;
  intentos_fallidos: number;
  bloqueado_hasta: string | null;
  ultimo_acceso: string | null;
  debe_cambiar_contrasena: boolean;
};

export type Supervisor = { id: string; nombre_completo: string; correo: string };

export type Evento = {
  id_evento: string;
  tipo: string;
  ocurrido_en: string;
  id_usuario: string;
  descripcion: string;
  datos: Record<string, unknown>;
};

export type Grupo = { clave: string; cantidad: number; total: string };
export type Resumen = { por_estado: Grupo[]; por_contrato: Grupo[] };
