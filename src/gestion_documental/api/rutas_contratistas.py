from typing import Annotated

from fastapi import APIRouter, Depends, status

from gestion_documental.api.dependencias import ServicioContratistasDep
from gestion_documental.api.esquemas import (
    ContratistaRespuesta,
    SolicitudContratista,
    SolicitudEdicionContratista,
)
from gestion_documental.api.seguridad import requiere_permiso
from gestion_documental.services.servicio_auth import Sesion

router = APIRouter(prefix="/contratistas", tags=["contratistas"])

PuedeConsultar = Annotated[Sesion, Depends(requiere_permiso("contratistas.consultar"))]
PuedeGestionar = Annotated[Sesion, Depends(requiere_permiso("contratistas.gestionar"))]


@router.get("")
def buscar(
    sesion: PuedeConsultar,
    servicio: ServicioContratistasDep,
    q: str | None = None,
    solo_activos: bool = False,
) -> list[ContratistaRespuesta]:
    return [ContratistaRespuesta.desde_dominio(c) for c in servicio.buscar(q, solo_activos)]


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    solicitud: SolicitudContratista, sesion: PuedeGestionar, servicio: ServicioContratistasDep
) -> ContratistaRespuesta:
    contratista = servicio.crear(id_usuario=sesion.id_usuario, **solicitud.model_dump())
    return ContratistaRespuesta.desde_dominio(contratista)


@router.get("/{id_contratista}")
def obtener(
    id_contratista: str, sesion: PuedeConsultar, servicio: ServicioContratistasDep
) -> ContratistaRespuesta:
    return ContratistaRespuesta.desde_dominio(servicio.obtener(id_contratista))


@router.patch("/{id_contratista}")
def editar(
    id_contratista: str,
    solicitud: SolicitudEdicionContratista,
    sesion: PuedeGestionar,
    servicio: ServicioContratistasDep,
) -> ContratistaRespuesta:
    contratista = servicio.editar(
        id_contratista, id_usuario=sesion.id_usuario, **solicitud.model_dump()
    )
    return ContratistaRespuesta.desde_dominio(contratista)


@router.post("/{id_contratista}/desactivar")
def desactivar(
    id_contratista: str, sesion: PuedeGestionar, servicio: ServicioContratistasDep
) -> ContratistaRespuesta:
    return ContratistaRespuesta.desde_dominio(
        servicio.desactivar(id_contratista, sesion.id_usuario)
    )


@router.post("/{id_contratista}/activar")
def activar(
    id_contratista: str, sesion: PuedeGestionar, servicio: ServicioContratistasDep
) -> ContratistaRespuesta:
    return ContratistaRespuesta.desde_dominio(servicio.activar(id_contratista, sesion.id_usuario))
