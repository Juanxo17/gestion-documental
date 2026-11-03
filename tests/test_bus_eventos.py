import logging

import pytest

from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.events.eventos import EstadoCuentaCambiado, EventoDominio
from gestion_documental.events.publicador import (
    BusEventosEnMemoria,
    EventPublisher,
    EventSubscriber,
)
from gestion_documental.events.suscriptores import NotificadorSupervisor, RegistroAuditoria
from tests.fabricas import cuenta_radicada, documento_adjuntado, estado_cambiado


class SuscriptorQueFalla(EventSubscriber):
    def manejar(self, evento: EventoDominio) -> None:
        raise RuntimeError("fallo sintético")


class ContadorPato:
    def __init__(self) -> None:
        self.recibidos = 0

    def manejar(self, evento: EventoDominio) -> None:
        self.recibidos += 1


def publicar_los_tres(bus: BusEventosEnMemoria) -> None:
    bus.publicar(cuenta_radicada())
    bus.publicar(estado_cambiado(EstadoCuenta.APROBADA))
    bus.publicar(documento_adjuntado())


def test_publisher_y_subscriber_no_se_pueden_instanciar() -> None:
    with pytest.raises(TypeError):
        EventPublisher()  # type: ignore[abstract]
    with pytest.raises(TypeError):
        EventSubscriber()  # type: ignore[abstract]


def test_bus_es_un_event_publisher() -> None:
    assert isinstance(BusEventosEnMemoria(), EventPublisher)


def test_auditoria_recibe_los_tres_tipos_y_notificador_solo_el_suyo() -> None:
    bus = BusEventosEnMemoria()
    auditoria = RegistroAuditoria()
    notificador = NotificadorSupervisor()
    bus.suscribir(EventoDominio, auditoria)
    bus.suscribir(EstadoCuentaCambiado, notificador)

    publicar_los_tres(bus)

    assert len(auditoria.lineas) == 3
    assert "[CuentaRadicada]" in auditoria.lineas[0]
    assert "[EstadoCuentaCambiado]" in auditoria.lineas[1]
    assert "[DocumentoAdjuntado]" in auditoria.lineas[2]
    assert notificador.mensajes == ("Supervisor: la cuenta RAD-SINT-0001 fue APROBADA",)


@pytest.mark.parametrize(
    ("estado", "notifica"),
    [
        (EstadoCuenta.APROBADA, True),
        (EstadoCuenta.RECHAZADA, True),
        (EstadoCuenta.ANULADA, False),
        (EstadoCuenta.PAGADA, False),
    ],
)
def test_notificador_solo_avisa_aprobada_o_rechazada(estado: EstadoCuenta, notifica: bool) -> None:
    bus = BusEventosEnMemoria()
    notificador = NotificadorSupervisor()
    bus.suscribir(EstadoCuentaCambiado, notificador)

    bus.publicar(estado_cambiado(estado))

    assert bool(notificador.mensajes) is notifica


def test_evento_sin_suscriptores_no_falla() -> None:
    BusEventosEnMemoria().publicar(cuenta_radicada())


def test_fallo_de_un_suscriptor_no_afecta_a_los_demas(caplog: pytest.LogCaptureFixture) -> None:
    bus = BusEventosEnMemoria()
    auditoria = RegistroAuditoria()
    bus.suscribir(EventoDominio, SuscriptorQueFalla())
    bus.suscribir(EventoDominio, auditoria)

    with caplog.at_level(logging.ERROR, logger="gestion_documental.events.publicador"):
        publicar_los_tres(bus)

    assert len(auditoria.lineas) == 3
    assert len(caplog.records) == 3
    assert "SuscriptorQueFalla" in caplog.records[0].getMessage()


def test_duck_typing_suscriptor_sin_herencia() -> None:
    bus = BusEventosEnMemoria()
    pato = ContadorPato()
    bus.suscribir(EventoDominio, pato)

    publicar_los_tres(bus)

    assert not isinstance(pato, EventSubscriber)
    assert pato.recibidos == 3
