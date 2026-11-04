from abc import ABC, abstractmethod
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from gestion_documental.domain.enums import (
    EstadoContrato,
    EstadoCuenta,
    OrigenDocumento,
    TipoDocumento,
)


class EventoDominio(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    id_evento: UUID = Field(default_factory=uuid4)
    ocurrido_en: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id_usuario: str = Field(min_length=1)

    @abstractmethod
    def describir(self) -> str: ...

    def __str__(self) -> str:
        return f"[{type(self).__name__}] {self.describir()}"


class CuentaRadicada(EventoDominio):
    numero_radicado: str = Field(min_length=1)
    id_contrato: str = Field(min_length=1)
    valor_cobro: Decimal = Field(gt=0, decimal_places=2)

    def describir(self) -> str:
        return (
            f"{self.id_usuario} radicó la cuenta {self.numero_radicado} "
            f"del contrato {self.id_contrato} por {self.valor_cobro}"
        )


class EstadoCuentaCambiado(EventoDominio):
    numero_radicado: str = Field(min_length=1)
    estado_anterior: EstadoCuenta
    estado_nuevo: EstadoCuenta
    observacion: str | None = Field(default=None, max_length=300)

    def describir(self) -> str:
        return (
            f"{self.id_usuario} cambió la cuenta {self.numero_radicado} "
            f"de {self.estado_anterior} a {self.estado_nuevo}"
        )


class DocumentoAdjuntado(EventoDominio):
    numero_radicado: str = Field(min_length=1)
    nombre_original: str = Field(min_length=1)
    origen: OrigenDocumento
    tipo: TipoDocumento

    def describir(self) -> str:
        return (
            f"{self.id_usuario} adjuntó {self.nombre_original} ({self.tipo}, {self.origen}) "
            f"a la cuenta {self.numero_radicado}"
        )


class CuentaPagada(EstadoCuentaCambiado):
    def describir(self) -> str:
        return f"{self.id_usuario} registró el pago de la cuenta {self.numero_radicado}"


class CuentaAnulada(EstadoCuentaCambiado):
    def describir(self) -> str:
        return (
            f"{self.id_usuario} anuló la cuenta {self.numero_radicado} "
            f"(estaba {self.estado_anterior})"
        )


class CuentaEditada(EventoDominio):
    numero_radicado: str = Field(min_length=1)
    campos: tuple[str, ...]

    def describir(self) -> str:
        return f"{self.id_usuario} editó la cuenta {self.numero_radicado}: {', '.join(self.campos)}"


class DocumentoEliminado(EventoDominio):
    numero_radicado: str = Field(min_length=1)
    id_documento: str = Field(min_length=1)
    nombre_original: str = Field(min_length=1)

    def describir(self) -> str:
        return (
            f"{self.id_usuario} eliminó {self.nombre_original} de la cuenta {self.numero_radicado}"
        )


class ContratoCambiado(EventoDominio):
    numero_contrato: str = Field(min_length=1)
    estado_anterior: EstadoContrato
    estado_nuevo: EstadoContrato

    def describir(self) -> str:
        return (
            f"{self.id_usuario} cambió el contrato {self.numero_contrato} "
            f"de {self.estado_anterior} a {self.estado_nuevo}"
        )
