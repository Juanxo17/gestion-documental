from functools import lru_cache
from typing import Annotated, Any

from fastapi import Depends
from pymongo.database import Database

from gestion_documental.events.eventos import EstadoCuentaCambiado, EventoDominio
from gestion_documental.events.publicador import BusEventosEnMemoria, EventPublisher
from gestion_documental.events.suscriptores import NotificadorSupervisor, RegistroAuditoria
from gestion_documental.repositories.conexion import get_db
from gestion_documental.repositories.mongo import RepositorioContratosMongo, RepositorioCuentasMongo
from gestion_documental.services.servicio_cuentas import ServicioCuentas


@lru_cache
def get_bus() -> EventPublisher:
    bus = BusEventosEnMemoria()
    bus.suscribir(EventoDominio, RegistroAuditoria())
    bus.suscribir(EstadoCuentaCambiado, NotificadorSupervisor())
    return bus


def get_servicio(
    db: Annotated[Database[dict[str, Any]], Depends(get_db)],
    bus: Annotated[EventPublisher, Depends(get_bus)],
) -> ServicioCuentas:
    return ServicioCuentas(RepositorioCuentasMongo(db), RepositorioContratosMongo(db), bus)
