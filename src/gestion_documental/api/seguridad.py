from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from pymongo.database import Database

from gestion_documental.config import get_config_auth
from gestion_documental.repositories.conexion import get_db
from gestion_documental.repositories.mongo import RepositorioRolesMongo, RepositorioUsuariosMongo
from gestion_documental.services.servicio_auth import (
    CambioContrasenaRequeridoError,
    ServicioAuth,
    Sesion,
)

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_servicio_auth(db: Annotated[Database[dict[str, Any]], Depends(get_db)]) -> ServicioAuth:
    config = get_config_auth()
    return ServicioAuth(
        RepositorioUsuariosMongo(db),
        RepositorioRolesMongo(db),
        secreto=config.jwt_secret,
        minutos_token=config.jwt_minutos,
    )


ServicioAuthDep = Annotated[ServicioAuth, Depends(get_servicio_auth)]


def usuario_actual(
    token: Annotated[str, Depends(esquema_oauth2)], servicio: ServicioAuthDep
) -> Sesion:
    return servicio.sesion_desde_token(token)


def usuario_habilitado(sesion: Annotated[Sesion, Depends(usuario_actual)]) -> Sesion:
    if sesion.usuario.debe_cambiar_contrasena:
        raise CambioContrasenaRequeridoError(
            "Debe cambiar su contraseña en POST /auth/cambiar-contrasena antes de continuar"
        )
    return sesion


def requiere_permiso(codigo: str) -> Callable[[Sesion], Sesion]:
    def verificar(sesion: Annotated[Sesion, Depends(usuario_habilitado)]) -> Sesion:
        sesion.exigir_permiso(codigo)
        return sesion

    return verificar
