from typing import Annotated, Any

from fastapi import Depends
from pwdlib import PasswordHash
from pymongo.database import Database

from gestion_documental.config import ConfiguracionAuth, get_config_auth
from gestion_documental.events.eventos import EstadoCuentaCambiado, EventoDominio
from gestion_documental.events.publicador import BusEventosEnMemoria, EventPublisher
from gestion_documental.events.suscriptores import NotificadorSupervisor
from gestion_documental.repositories.base import Repositorios
from gestion_documental.repositories.conexion import get_db
from gestion_documental.repositories.mongo import repositorios_mongo
from gestion_documental.services.servicio_auth import ServicioAuth, hasher_por_defecto
from gestion_documental.services.servicio_contratistas import ServicioContratistas
from gestion_documental.services.servicio_contratos import ServicioContratos
from gestion_documental.services.servicio_cuentas import ServicioCuentas
from gestion_documental.services.servicio_usuarios import ServicioUsuarios


def get_repositorios(db: Annotated[Database[dict[str, Any]], Depends(get_db)]) -> Repositorios:
    return repositorios_mongo(db)


def get_hasher() -> PasswordHash:
    return hasher_por_defecto()


Repos = Annotated[Repositorios, Depends(get_repositorios)]
Hasher = Annotated[PasswordHash, Depends(get_hasher)]


def get_bus(repos: Repos) -> EventPublisher:
    bus = BusEventosEnMemoria()
    bus.suscribir(EventoDominio, repos.auditoria)
    bus.suscribir(EstadoCuentaCambiado, NotificadorSupervisor())
    return bus


Bus = Annotated[EventPublisher, Depends(get_bus)]


def get_servicio_cuentas(repos: Repos, bus: Bus) -> ServicioCuentas:
    return ServicioCuentas(repos.cuentas, repos.contratos, repos.contratistas, repos.archivos, bus)


def get_servicio_auth(
    repos: Repos,
    config: Annotated[ConfiguracionAuth, Depends(get_config_auth)],
    hasher: Hasher,
) -> ServicioAuth:
    return ServicioAuth(
        repos.usuarios,
        repos.roles,
        secreto=config.jwt_secret,
        minutos_token=config.jwt_minutos,
        hasher=hasher,
    )


def get_servicio_usuarios(repos: Repos, hasher: Hasher) -> ServicioUsuarios:
    return ServicioUsuarios(repos.usuarios, repos.roles, hasher)


def get_servicio_contratistas(repos: Repos) -> ServicioContratistas:
    return ServicioContratistas(repos.contratistas)


def get_servicio_contratos(repos: Repos, bus: Bus) -> ServicioContratos:
    return ServicioContratos(
        repos.contratos, repos.contratistas, repos.usuarios, repos.roles, repos.cuentas, bus
    )


ServicioCuentasDep = Annotated[ServicioCuentas, Depends(get_servicio_cuentas)]
ServicioAuthDep = Annotated[ServicioAuth, Depends(get_servicio_auth)]
ServicioUsuariosDep = Annotated[ServicioUsuarios, Depends(get_servicio_usuarios)]
ServicioContratistasDep = Annotated[ServicioContratistas, Depends(get_servicio_contratistas)]
ServicioContratosDep = Annotated[ServicioContratos, Depends(get_servicio_contratos)]
