from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.events.eventos import EstadoCuentaCambiado, EventoDominio
from gestion_documental.events.publicador import EventSubscriber

ESTADOS_NOTIFICABLES = frozenset({EstadoCuenta.APROBADA, EstadoCuenta.RECHAZADA})


class RegistroAuditoria(EventSubscriber):
    def __init__(self) -> None:
        self._lineas: list[str] = []

    @property
    def lineas(self) -> tuple[str, ...]:
        return tuple(self._lineas)

    def manejar(self, evento: EventoDominio) -> None:
        self._lineas.append(f"{evento.ocurrido_en.isoformat()} {evento}")


class NotificadorSupervisor(EventSubscriber):
    def __init__(self) -> None:
        self._mensajes: list[str] = []

    @property
    def mensajes(self) -> tuple[str, ...]:
        return tuple(self._mensajes)

    def manejar(self, evento: EventoDominio) -> None:
        if not isinstance(evento, EstadoCuentaCambiado):
            return
        if evento.estado_nuevo in ESTADOS_NOTIFICABLES:
            self._mensajes.append(
                f"Supervisor: la cuenta {evento.numero_radicado} fue {evento.estado_nuevo}"
            )
