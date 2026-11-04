from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from gestion_documental.api.esquemas import (
    SolicitudCambioContrasena,
    TokenRespuesta,
    UsuarioActualRespuesta,
)
from gestion_documental.api.seguridad import ServicioAuthDep, usuario_actual
from gestion_documental.services.servicio_auth import Sesion

router = APIRouter(prefix="/auth", tags=["auth"])

SesionActual = Annotated[Sesion, Depends(usuario_actual)]


@router.post("/login")
def login(
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()], servicio: ServicioAuthDep
) -> TokenRespuesta:
    return TokenRespuesta(access_token=servicio.login(formulario.username, formulario.password))


@router.get("/me")
def me(sesion: SesionActual, servicio: ServicioAuthDep) -> UsuarioActualRespuesta:
    usuario = sesion.usuario
    return UsuarioActualRespuesta(
        id=sesion.id_usuario,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        correo=usuario.correo,
        cargo=usuario.cargo,
        rol=sesion.rol.nombre,
        permisos=sorted(servicio.obtener_permisos(sesion.id_usuario)),
        debe_cambiar_contrasena=usuario.debe_cambiar_contrasena,
    )


@router.post("/cambiar-contrasena", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_contrasena(
    solicitud: SolicitudCambioContrasena, sesion: SesionActual, servicio: ServicioAuthDep
) -> Response:
    servicio.cambiar_contrasena(
        sesion.id_usuario, solicitud.contrasena_actual, solicitud.contrasena_nueva
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
