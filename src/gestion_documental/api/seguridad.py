from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from gestion_documental.api.dependencias import ServicioAuthDep
from gestion_documental.services.servicio_auth import (
    CambioContrasenaRequeridoError,
    PermisoDenegadoError,
    Sesion,
)

esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


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


def requiere_rol(nombre: str) -> Callable[[Sesion], Sesion]:
    def verificar(sesion: Annotated[Sesion, Depends(usuario_habilitado)]) -> Sesion:
        if sesion.rol.nombre != nombre or not sesion.rol.activo:
            raise PermisoDenegadoError(f"Solo el rol {nombre} puede usar esta operación")
        return sesion

    return verificar
