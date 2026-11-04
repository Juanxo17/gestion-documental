from abc import abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from gestion_documental.events.eventos import EventoDominio
from gestion_documental.events.publicador import EventSubscriber

CAMPOS_COMUNES = {"id_evento", "ocurrido_en", "id_usuario"}


@dataclass(frozen=True, kw_only=True)
class RegistroEvento:
    id_evento: str
    tipo: str
    ocurrido_en: datetime
    id_usuario: str
    descripcion: str
    datos: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def desde_evento(cls, evento: EventoDominio) -> RegistroEvento:
        return cls(
            id_evento=str(evento.id_evento),
            tipo=type(evento).__name__,
            ocurrido_en=evento.ocurrido_en,
            id_usuario=evento.id_usuario,
            descripcion=evento.describir(),
            datos=evento.model_dump(mode="json", exclude=CAMPOS_COMUNES),
        )


@dataclass(frozen=True, kw_only=True)
class FiltroAuditoria:
    tipo: str | None = None
    id_usuario: str | None = None
    desde: datetime | None = None
    hasta: datetime | None = None
    limite: int = 100

    def admite(self, registro: RegistroEvento) -> bool:
        return (
            (self.tipo is None or registro.tipo == self.tipo)
            and (self.id_usuario is None or registro.id_usuario == self.id_usuario)
            and (self.desde is None or registro.ocurrido_en >= self.desde)
            and (self.hasta is None or registro.ocurrido_en <= self.hasta)
        )


class AuditoriaPersistente(EventSubscriber):
    def manejar(self, evento: EventoDominio) -> None:
        self.registrar(RegistroEvento.desde_evento(evento))

    @abstractmethod
    def registrar(self, registro: RegistroEvento) -> None: ...

    @abstractmethod
    def buscar(self, filtro: FiltroAuditoria) -> list[RegistroEvento]: ...


class AuditoriaEnMemoria(AuditoriaPersistente):
    def __init__(self) -> None:
        self._registros: list[RegistroEvento] = []

    def registrar(self, registro: RegistroEvento) -> None:
        self._registros.append(registro)

    def buscar(self, filtro: FiltroAuditoria) -> list[RegistroEvento]:
        encontrados = [registro for registro in self._registros if filtro.admite(registro)]
        encontrados.sort(key=lambda registro: registro.ocurrido_en, reverse=True)
        return encontrados[: filtro.limite]
