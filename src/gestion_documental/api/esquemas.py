from datetime import date, datetime
from decimal import Decimal
from typing import Self

from pydantic import BaseModel, ConfigDict, Field

from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento


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


class SolicitudCambioEstado(Solicitud):
    nuevo_estado: EstadoCuenta
    observacion: str | None = Field(default=None, max_length=300)


class SolicitudCambioContrasena(BaseModel):
    contrasena_actual: str
    contrasena_nueva: str


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


class DocumentoRespuesta(BaseModel):
    nombre_original: str
    ruta_archivo: str
    tipo: TipoDocumento
    origen: OrigenDocumento
    descripcion: str


class CambioRespuesta(BaseModel):
    estado_anterior: EstadoCuenta | None
    estado_nuevo: EstadoCuenta
    id_usuario: str
    fecha_cambio: datetime
    observacion: str | None


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
            documentos=[
                DocumentoRespuesta(
                    nombre_original=documento.nombre_original,
                    ruta_archivo=documento.ruta_archivo,
                    tipo=documento.tipo,
                    origen=documento.origen,
                    descripcion=documento.describir(),
                )
                for documento in cuenta.documentos
            ],
            historial=[
                CambioRespuesta(
                    estado_anterior=cambio.estado_anterior,
                    estado_nuevo=cambio.estado_nuevo,
                    id_usuario=cambio.id_usuario,
                    fecha_cambio=cambio.fecha_cambio,
                    observacion=cambio.observacion,
                )
                for cambio in cuenta.historial
            ],
        )
