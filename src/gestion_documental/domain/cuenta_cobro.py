from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Final

from gestion_documental.domain.documentos import Documento
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.domain.errores import (
    ErrorDominio,
    NoEncontradoError,
    TransicionInvalidaError,
)
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
ESTADOS_EDITABLES: Final = frozenset({EstadoCuenta.RECIBIDA, EstadoCuenta.EN_REVISION})


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

    @property
    def es_editable(self) -> bool:
        return self.estado in ESTADOS_EDITABLES

    def verificar_editable(self) -> None:
        if not self.es_editable:
            raise ErrorDominio(
                f"La cuenta está {self.estado}; solo se modifica en RECIBIDA o EN_REVISION"
            )

    def editar(
        self,
        *,
        numero_cuenta: str | None = None,
        valor_cobro: ValorMonetario | None = None,
        concepto_pago: str | None = None,
        fecha_presentacion: date | None = None,
        observaciones: str | None = None,
    ) -> list[str]:
        self.verificar_editable()
        cambios: dict[str, object] = {
            "numero_cuenta": numero_cuenta,
            "valor_cobro": valor_cobro,
            "concepto_pago": concepto_pago,
            "fecha_presentacion": fecha_presentacion,
            "observaciones": observaciones,
        }
        modificados = [
            campo
            for campo, valor in cambios.items()
            if valor is not None and valor != getattr(self, campo)
        ]
        for campo in ("numero_cuenta", "concepto_pago"):
            if campo in modificados and not str(cambios[campo]).strip():
                raise ErrorDominio(f"La cuenta necesita {campo}")
        for campo in modificados:
            setattr(self, campo, cambios[campo])
        return modificados

    def documento(self, id_documento: str) -> Documento:
        for documento in self._documentos:
            if documento.id_documento == id_documento:
                return documento
        raise NoEncontradoError(
            f"La cuenta {self.numero_radicado} no tiene el documento {id_documento}"
        )

    def eliminar_documento(self, id_documento: str) -> Documento:
        self.verificar_editable()
        documento = self.documento(id_documento)
        self._documentos.remove(documento)
        return documento

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
