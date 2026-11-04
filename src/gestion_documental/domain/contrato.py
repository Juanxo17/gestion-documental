from dataclasses import dataclass
from datetime import date

from gestion_documental.domain.enums import EstadoContrato
from gestion_documental.domain.errores import ErrorDominio
from gestion_documental.domain.valores import ValorMonetario


@dataclass(kw_only=True)
class Contrato:
    numero_contrato: str
    id_contratista: str
    objeto_contrato: str
    valor_total: ValorMonetario
    fecha_inicio: date
    fecha_fin: date
    id_supervisor: str
    estado: EstadoContrato = EstadoContrato.ACTIVO
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.numero_contrato.strip():
            raise ErrorDominio("El contrato necesita numero_contrato")
        if not self.objeto_contrato.strip():
            raise ErrorDominio("El contrato necesita objeto_contrato")
        if self.fecha_fin < self.fecha_inicio:
            raise ErrorDominio("fecha_fin no puede ser anterior a fecha_inicio")
