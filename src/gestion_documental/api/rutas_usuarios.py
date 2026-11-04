from typing import Annotated

from fastapi import APIRouter, Depends, status

from gestion_documental.api.dependencias import ServicioUsuariosDep
from gestion_documental.api.esquemas import (
    SolicitudEdicionUsuario,
    SolicitudRol,
    SolicitudUsuario,
    UsuarioCreadoRespuesta,
    UsuarioRespuesta,
)
from gestion_documental.api.seguridad import requiere_permiso
from gestion_documental.domain.usuarios import Usuario
from gestion_documental.services.servicio_auth import Sesion
from gestion_documental.services.servicio_usuarios import ServicioUsuarios

router = APIRouter(prefix="/usuarios", tags=["usuarios"])

PuedeGestionar = Annotated[Sesion, Depends(requiere_permiso("usuarios.gestionar"))]


def respuesta(servicio: ServicioUsuarios, usuario: Usuario) -> UsuarioRespuesta:
    return UsuarioRespuesta.desde_dominio(usuario, servicio.rol(usuario.id_rol))


@router.get("")
def listar(sesion: PuedeGestionar, servicio: ServicioUsuariosDep) -> list[UsuarioRespuesta]:
    return [respuesta(servicio, usuario) for usuario in servicio.listar()]


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    solicitud: SolicitudUsuario, sesion: PuedeGestionar, servicio: ServicioUsuariosDep
) -> UsuarioCreadoRespuesta:
    usuario, temporal = servicio.crear(**solicitud.model_dump())
    return UsuarioCreadoRespuesta(
        usuario=respuesta(servicio, usuario), contrasena_temporal=temporal
    )


@router.get("/{id_usuario}")
def obtener(
    id_usuario: str, sesion: PuedeGestionar, servicio: ServicioUsuariosDep
) -> UsuarioRespuesta:
    return respuesta(servicio, servicio.obtener(id_usuario))


@router.patch("/{id_usuario}")
def editar(
    id_usuario: str,
    solicitud: SolicitudEdicionUsuario,
    sesion: PuedeGestionar,
    servicio: ServicioUsuariosDep,
) -> UsuarioRespuesta:
    return respuesta(servicio, servicio.editar(id_usuario, **solicitud.model_dump()))


@router.put("/{id_usuario}/rol")
def cambiar_rol(
    id_usuario: str,
    solicitud: SolicitudRol,
    sesion: PuedeGestionar,
    servicio: ServicioUsuariosDep,
) -> UsuarioRespuesta:
    return respuesta(servicio, servicio.cambiar_rol(id_usuario, solicitud.rol))


@router.post("/{id_usuario}/desactivar")
def desactivar(
    id_usuario: str, sesion: PuedeGestionar, servicio: ServicioUsuariosDep
) -> UsuarioRespuesta:
    return respuesta(servicio, servicio.desactivar(id_usuario, sesion.id_usuario))


@router.post("/{id_usuario}/reiniciar-bloqueo")
def reiniciar_bloqueo(
    id_usuario: str, sesion: PuedeGestionar, servicio: ServicioUsuariosDep
) -> UsuarioRespuesta:
    return respuesta(servicio, servicio.reiniciar_bloqueo(id_usuario))
