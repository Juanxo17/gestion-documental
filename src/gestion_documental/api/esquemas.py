from datetime import date, datetime
from decimal import Decimal
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CambioEstado, CuentaCobro
from gestion_documental.domain.documentos import Documento, DocumentoLocal
from gestion_documental.domain.enums import (
    EstadoContrato,
    EstadoCuenta,
    OrigenDocumento,
    TipoDocumento,
    TipoPersona,
)
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.events.auditoria import RegistroEvento
from gestion_documental.repositories.base import ResumenGrupo


class Solicitud(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class SolicitudRadicacion(Solicitud):
    numero_radicado: str
    numero_cuenta: str
    numero_contrato: str
    valor_cobro: Decimal
    concepto_pago: str
    fecha_presentacion: date
    observaciones: str | None = None


class SolicitudEdicionCuenta(Solicitud):
    numero_cuenta: str | None = None
    valor_cobro: Decimal | None = None
    concepto_pago: str | None = None
    fecha_presentacion: date | None = None
    observaciones: str | None = None


class SolicitudCambioEstado(Solicitud):
    nuevo_estado: EstadoCuenta
    observacion: str | None = Field(default=None, max_length=300)


class SolicitudObservacion(Solicitud):
    observacion: str | None = Field(default=None, max_length=300)


class SolicitudDocumentoUrl(Solicitud):
    nombre_original: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    tipo: TipoDocumento


class SolicitudCambioContrasena(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str


class SolicitudUsuario(Solicitud):
    nombre: str = Field(min_length=1)
    apellido: str = Field(min_length=1)
    correo: str = Field(min_length=3)
    cargo: str = Field(min_length=1)
    rol: str = Field(min_length=1)


class SolicitudEdicionUsuario(Solicitud):
    nombre: str | None = None
    apellido: str | None = None
    correo: str | None = None
    cargo: str | None = None


class SolicitudRol(Solicitud):
    rol: str = Field(min_length=1)


class SolicitudContratista(Solicitud):
    tipo_persona: TipoPersona
    nombre_completo: str = Field(min_length=1)
    nit_cedula: str = Field(min_length=1)
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None


class SolicitudEdicionContratista(Solicitud):
    nombre_completo: str | None = None
    nit_cedula: str | None = None
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None


class SolicitudContrato(Solicitud):
    numero_contrato: str = Field(min_length=1, max_length=50)
    nit_contratista: str = Field(min_length=1)
    objeto_contrato: str = Field(min_length=1)
    valor_total: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    fecha_inicio: date
    fecha_fin: date
    id_supervisor: str = Field(min_length=1)


class SolicitudEdicionContrato(Solicitud):
    objeto_contrato: str | None = None
    valor_total: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    id_supervisor: str | None = None


class SolicitudEstadoContrato(Solicitud):
    nuevo_estado: EstadoContrato


class TokenRespuesta(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UsuarioActualRespuesta(BaseModel):
    id: str
    nombre: str
    apellido: str
    correo: str
    cargo: str
    rol: str
    permisos: list[str]
    debe_cambiar_contrasena: bool


class UsuarioRespuesta(BaseModel):
    id: str
    nombre: str
    apellido: str
    correo: str
    cargo: str
    rol: str
    activo: bool
    intentos_fallidos: int
    bloqueado_hasta: datetime | None
    ultimo_acceso: datetime | None
    debe_cambiar_contrasena: bool

    @classmethod
    def desde_dominio(cls, usuario: Usuario, rol: Rol) -> Self:
        assert usuario.id is not None
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            apellido=usuario.apellido,
            correo=usuario.correo,
            cargo=usuario.cargo,
            rol=rol.nombre,
            activo=usuario.activo,
            intentos_fallidos=usuario.intentos_fallidos,
            bloqueado_hasta=usuario.bloqueado_hasta,
            ultimo_acceso=usuario.ultimo_acceso,
            debe_cambiar_contrasena=usuario.debe_cambiar_contrasena,
        )


class SupervisorRespuesta(BaseModel):
    id: str
    nombre_completo: str
    correo: str


class UsuarioCreadoRespuesta(BaseModel):
    usuario: UsuarioRespuesta
    contrasena_temporal: str


class ContratistaRespuesta(BaseModel):
    id: str
    tipo_persona: TipoPersona
    nombre_completo: str
    nit_cedula: str
    telefono: str | None
    correo: str | None
    direccion: str | None
    activo: bool

    @classmethod
    def desde_dominio(cls, contratista: Contratista) -> Self:
        assert contratista.id is not None
        return cls(
            id=contratista.id,
            tipo_persona=contratista.tipo_persona,
            nombre_completo=contratista.nombre_completo,
            nit_cedula=contratista.nit_cedula,
            telefono=contratista.telefono,
            correo=contratista.correo,
            direccion=contratista.direccion,
            activo=contratista.activo,
        )


class ContratoRespuesta(BaseModel):
    id: str
    numero_contrato: str
    id_contratista: str
    objeto_contrato: str
    valor_total: Decimal
    fecha_inicio: date
    fecha_fin: date
    estado: EstadoContrato
    id_supervisor: str

    @classmethod
    def desde_dominio(cls, contrato: Contrato) -> Self:
        assert contrato.id is not None
        return cls(
            id=contrato.id,
            numero_contrato=contrato.numero_contrato,
            id_contratista=contrato.id_contratista,
            objeto_contrato=contrato.objeto_contrato,
            valor_total=contrato.valor_total.monto,
            fecha_inicio=contrato.fecha_inicio,
            fecha_fin=contrato.fecha_fin,
            estado=contrato.estado,
            id_supervisor=contrato.id_supervisor,
        )


class DocumentoRespuesta(BaseModel):
    id_documento: str
    nombre_original: str
    ruta_archivo: str
    tipo: TipoDocumento
    origen: OrigenDocumento
    tipo_mime: str | None
    tamano_bytes: int | None
    hash_sha256: str | None
    descripcion: str

    @classmethod
    def desde_dominio(cls, documento: Documento) -> Self:
        local = documento if isinstance(documento, DocumentoLocal) else None
        return cls(
            id_documento=documento.id_documento,
            nombre_original=documento.nombre_original,
            ruta_archivo=documento.ruta_archivo,
            tipo=documento.tipo,
            origen=documento.origen,
            tipo_mime=local.tipo_mime if local else None,
            tamano_bytes=local.tamano_bytes if local else None,
            hash_sha256=local.hash_sha256 if local else None,
            descripcion=documento.describir(),
        )


class CambioRespuesta(BaseModel):
    estado_anterior: EstadoCuenta | None
    estado_nuevo: EstadoCuenta
    id_usuario: str
    fecha_cambio: datetime
    observacion: str | None

    @classmethod
    def desde_dominio(cls, cambio: CambioEstado) -> Self:
        return cls(
            estado_anterior=cambio.estado_anterior,
            estado_nuevo=cambio.estado_nuevo,
            id_usuario=cambio.id_usuario,
            fecha_cambio=cambio.fecha_cambio,
            observacion=cambio.observacion,
        )


class CuentaRespuesta(BaseModel):
    numero_radicado: str
    numero_cuenta: str
    id_contrato: str
    valor_cobro: Decimal
    concepto_pago: str
    fecha_presentacion: date
    estado: EstadoCuenta
    observaciones: str | None
    documentos: list[DocumentoRespuesta]
    historial: list[CambioRespuesta]

    @classmethod
    def desde_dominio(cls, cuenta: CuentaCobro) -> Self:
        return cls(
            numero_radicado=cuenta.numero_radicado,
            numero_cuenta=cuenta.numero_cuenta,
            id_contrato=cuenta.id_contrato,
            valor_cobro=cuenta.valor_cobro.monto,
            concepto_pago=cuenta.concepto_pago,
            fecha_presentacion=cuenta.fecha_presentacion,
            estado=cuenta.estado,
            observaciones=cuenta.observaciones,
            documentos=[DocumentoRespuesta.desde_dominio(d) for d in cuenta.documentos],
            historial=[CambioRespuesta.desde_dominio(c) for c in cuenta.historial],
        )


class PaginaCuentasRespuesta(BaseModel):
    total: int
    pagina: int
    tamano: int
    items: list[CuentaRespuesta]


class EventoRespuesta(BaseModel):
    id_evento: str
    tipo: str
    ocurrido_en: datetime
    id_usuario: str
    descripcion: str
    datos: dict[str, Any]

    @classmethod
    def desde_dominio(cls, registro: RegistroEvento) -> Self:
        return cls(
            id_evento=registro.id_evento,
            tipo=registro.tipo,
            ocurrido_en=registro.ocurrido_en,
            id_usuario=registro.id_usuario,
            descripcion=registro.descripcion,
            datos=registro.datos,
        )


class GrupoResumen(BaseModel):
    clave: str
    cantidad: int
    total: Decimal

    @classmethod
    def desde_dominio(cls, grupo: ResumenGrupo) -> Self:
        return cls(clave=grupo.clave, cantidad=grupo.cantidad, total=grupo.total)


class ResumenRespuesta(BaseModel):
    por_estado: list[GrupoResumen]
    por_contrato: list[GrupoResumen]


class ErrorRespuesta(BaseModel):
    error: str
    detalle: str
