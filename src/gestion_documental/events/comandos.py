from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento


class Comando(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)

    id_usuario: str = Field(min_length=1)


class RadicarCuenta(Comando):
    numero_radicado: str = Field(min_length=1, max_length=30)
    numero_cuenta: str = Field(min_length=1, max_length=30)
    numero_contrato: str = Field(min_length=1, max_length=50)
    valor_cobro: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    concepto_pago: str = Field(min_length=1)
    fecha_presentacion: date
    observaciones: str | None = None


class CambiarEstadoCuenta(Comando):
    numero_radicado: str = Field(min_length=1)
    nuevo_estado: EstadoCuenta
    observacion: str | None = Field(default=None, max_length=300)


class AdjuntarDocumento(Comando):
    numero_radicado: str = Field(min_length=1)
    nombre_original: str = Field(min_length=1, max_length=255)
    ruta_archivo: str = Field(min_length=1, max_length=300)
    tipo: TipoDocumento
    origen: OrigenDocumento
    tipo_mime: str | None = Field(default=None, max_length=100)
    hash_sha256: str | None = None
    tamano_bytes: int | None = Field(default=None, gt=0)
