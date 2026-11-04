from dataclasses import dataclass
from datetime import date
from typing import Final

from gestion_documental.domain.enums import EstadoContrato
from gestion_documental.domain.errores import ErrorDominio, TransicionInvalidaError
from gestion_documental.domain.valores import ValorMonetario

TRANSICIONES_CONTRATO: Final[dict[EstadoContrato, frozenset[EstadoContrato]]] = {
    EstadoContrato.ACTIVO: frozenset(
        {EstadoContrato.SUSPENDIDO, EstadoContrato.TERMINADO, EstadoContrato.CANCELADO}
    ),
    EstadoContrato.SUSPENDIDO: frozenset({EstadoContrato.ACTIVO, EstadoContrato.CANCELADO}),
    EstadoContrato.TERMINADO: frozenset({EstadoContrato.LIQUIDADO}),
    EstadoContrato.LIQUIDADO: frozenset(),
    EstadoContrato.CANCELADO: frozenset(),
}


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
        self.validar()

    def validar(self) -> None:
        if not self.numero_contrato.strip():
            raise ErrorDominio("El contrato necesita numero_contrato")
        if not self.objeto_contrato.strip():
            raise ErrorDominio("El contrato necesita objeto_contrato")
        if self.fecha_fin < self.fecha_inicio:
            raise ErrorDominio("fecha_fin no puede ser anterior a fecha_inicio")

    def esta_vigente(self, fecha: date) -> bool:
        return self.fecha_inicio <= fecha <= self.fecha_fin

    def verificar_radicacion(self, fecha_presentacion: date) -> None:
        if self.estado is not EstadoContrato.ACTIVO:
            raise ErrorDominio(
                f"El contrato {self.numero_contrato} está {self.estado}; solo se radica en ACTIVO"
            )
        if not self.esta_vigente(fecha_presentacion):
            raise ErrorDominio(
                f"La fecha {fecha_presentacion} está fuera de la vigencia del contrato "
                f"({self.fecha_inicio} a {self.fecha_fin})"
            )

    def cambiar_estado(self, nuevo: EstadoContrato) -> EstadoContrato:
        if nuevo not in TRANSICIONES_CONTRATO[self.estado]:
            raise TransicionInvalidaError(f"El contrato no puede pasar de {self.estado} a {nuevo}")
        anterior = self.estado
        self.estado = nuevo
        return anterior
