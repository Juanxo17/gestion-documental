from typing import Annotated

from fastapi import APIRouter, Depends, status

from gestion_documental.api.dependencias import ServicioContratosDep
from gestion_documental.api.esquemas import (
    ContratoRespuesta,
    SolicitudContrato,
    SolicitudEdicionContrato,
    SolicitudEstadoContrato,
)
from gestion_documental.api.seguridad import requiere_permiso
from gestion_documental.domain.enums import EstadoContrato
from gestion_documental.services.servicio_auth import Sesion

router = APIRouter(prefix="/contratos", tags=["contratos"])

PuedeConsultar = Annotated[Sesion, Depends(requiere_permiso("contratos.consultar"))]
PuedeGestionar = Annotated[Sesion, Depends(requiere_permiso("contratos.gestionar"))]


@router.get("")
def listar(
    sesion: PuedeConsultar, servicio: ServicioContratosDep, estado: EstadoContrato | None = None
) -> list[ContratoRespuesta]:
    return [ContratoRespuesta.desde_dominio(c) for c in servicio.listar(estado)]


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    solicitud: SolicitudContrato, sesion: PuedeGestionar, servicio: ServicioContratosDep
) -> ContratoRespuesta:
    return ContratoRespuesta.desde_dominio(servicio.crear(**solicitud.model_dump()))


@router.get("/{numero_contrato}")
def obtener(
    numero_contrato: str, sesion: PuedeConsultar, servicio: ServicioContratosDep
) -> ContratoRespuesta:
    return ContratoRespuesta.desde_dominio(servicio.obtener(numero_contrato))


@router.patch("/{numero_contrato}")
def editar(
    numero_contrato: str,
    solicitud: SolicitudEdicionContrato,
    sesion: PuedeGestionar,
    servicio: ServicioContratosDep,
) -> ContratoRespuesta:
    return ContratoRespuesta.desde_dominio(
        servicio.editar(numero_contrato, **solicitud.model_dump())
    )


@router.post("/{numero_contrato}/estado")
def cambiar_estado(
    numero_contrato: str,
    solicitud: SolicitudEstadoContrato,
    sesion: PuedeGestionar,
    servicio: ServicioContratosDep,
) -> ContratoRespuesta:
    contrato = servicio.cambiar_estado(numero_contrato, solicitud.nuevo_estado, sesion.id_usuario)
    return ContratoRespuesta.desde_dominio(contrato)
