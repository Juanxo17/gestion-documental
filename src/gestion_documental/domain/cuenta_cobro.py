from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Final

from gestion_documental.domain.documentos import Documento
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.domain.errores import ErrorDominio, TransicionInvalidaError
from gestion_documental.domain.tiempo import ahora_utc
from gestion_documental.domain.valores import ValorMonetario

TRANSICIONES: Final[dict[EstadoCuenta, frozenset[EstadoCuenta]]] = {
    EstadoCuenta.RECIBIDA: frozenset({EstadoCuenta.EN_REVISION, EstadoCuenta.ANULADA}),
    EstadoCuenta.EN_REVISION: frozenset(
        {EstadoCuenta.APROBADA, EstadoCuenta.RECHAZADA, EstadoCuenta.ANULADA}
    ),
    EstadoCuenta.APROBADA: frozenset({EstadoCuenta.PAGADA, EstadoCuenta.ANULADA}),
    EstadoCuenta.RECHAZADA: frozenset(),
    EstadoCuenta.PAGADA: frozenset(),
    EstadoCuenta.ANULADA: frozenset(),
}


@dataclass(frozen=True, kw_only=True)
class CambioEstado:
    estado_anterior: EstadoCuenta | None
    estado_nuevo: EstadoCuenta
    id_usuario: str
    observacion: str | None = None
    fecha_cambio: datetime = field(default_factory=ahora_utc)


class CuentaCobro:
    def __init__(
        self,
        *,
        numero_radicado: str,
        numero_cuenta: str,
        id_contrato: str,
        valor_cobro: ValorMonetario,
        concepto_pago: str,
        fecha_presentacion: date,
        id_usuario: str,
        observaciones: str | None = None,
        documentos: Iterable[Documento] = (),
        historial: Iterable[CambioEstado] = (),
    ) -> None:
        if not numero_radicado.strip():
            raise ErrorDominio("La cuenta necesita numero_radicado")
        if not numero_cuenta.strip():
            raise ErrorDominio("La cuenta necesita numero_cuenta")
        if not concepto_pago.strip():
            raise ErrorDominio("La cuenta necesita concepto_pago")

        self.numero_radicado = numero_radicado
        self.numero_cuenta = numero_cuenta
        self.id_contrato = id_contrato
        self.valor_cobro = valor_cobro
        self.concepto_pago = concepto_pago
        self.fecha_presentacion = fecha_presentacion
        self.id_usuario = id_usuario
        self.observaciones = observaciones
        self._documentos: list[Documento] = list(documentos)
        self._historial: list[CambioEstado] = list(historial) or [
            CambioEstado(
                estado_anterior=None,
                estado_nuevo=EstadoCuenta.RECIBIDA,
                id_usuario=id_usuario,
                observacion="Cuenta radicada",
            )
        ]
        if self._historial[0].estado_anterior is not None:
            raise ErrorDominio("El primer registro del historial no puede tener estado anterior")

    @property
    def estado(self) -> EstadoCuenta:
        return self._historial[-1].estado_nuevo

    @property
    def es_final(self) -> bool:
        return not TRANSICIONES[self.estado]

    @property
    def documentos(self) -> tuple[Documento, ...]:
        return tuple(self._documentos)

    @property
    def historial(self) -> tuple[CambioEstado, ...]:
        return tuple(self._historial)

    def agregar_documento(self, documento: Documento) -> None:
        if self.es_final:
            raise ErrorDominio(f"No se pueden agregar documentos a una cuenta {self.estado}")
        documento.validar()
        self._documentos.append(documento)

    def cambiar_estado(
        self, nuevo: EstadoCuenta, id_usuario: str, observacion: str | None = None
    ) -> CambioEstado:
        if nuevo not in TRANSICIONES[self.estado]:
            raise TransicionInvalidaError(f"No se puede pasar de {self.estado} a {nuevo}")
        cambio = CambioEstado(
            estado_anterior=self.estado,
            estado_nuevo=nuevo,
            id_usuario=id_usuario,
            observacion=observacion,
        )
        self._historial.append(cambio)
        return cambio
