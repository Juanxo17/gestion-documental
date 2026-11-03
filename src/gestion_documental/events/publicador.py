import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Protocol

from gestion_documental.events.eventos import EventoDominio

logger = logging.getLogger(__name__)


class ManejadorEventos(Protocol):
    def manejar(self, evento: EventoDominio) -> None: ...


class EventSubscriber(ABC):
    @abstractmethod
    def manejar(self, evento: EventoDominio) -> None: ...


class EventPublisher(ABC):
    @abstractmethod
    def suscribir(self, tipo_evento: type[EventoDominio], suscriptor: ManejadorEventos) -> None: ...

    @abstractmethod
    def publicar(self, evento: EventoDominio) -> None: ...


class BusEventosEnMemoria(EventPublisher):
    def __init__(self) -> None:
        self._suscriptores: defaultdict[type[Any], list[ManejadorEventos]] = defaultdict(list)

    def suscribir(self, tipo_evento: type[EventoDominio], suscriptor: ManejadorEventos) -> None:
        self._suscriptores[tipo_evento].append(suscriptor)

    def publicar(self, evento: EventoDominio) -> None:
        for tipo in type(evento).__mro__:
            for suscriptor in self._suscriptores.get(tipo, []):
                try:
                    suscriptor.manejar(evento)
                except Exception:
                    logger.exception(
                        "El suscriptor %s falló al manejar %s",
                        type(suscriptor).__name__,
                        type(evento).__name__,
                    )
