from typing import Annotated

from fastapi import APIRouter, Depends, status

from gestion_documental.api.dependencias import get_servicio
from gestion_documental.api.esquemas import (
    CuentaRespuesta,
    SolicitudCambioEstado,
    SolicitudRadicacion,
)
from gestion_documental.api.seguridad import requiere_permiso
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.events.comandos import CambiarEstadoCuenta, RadicarCuenta
from gestion_documental.services.servicio_auth import Sesion
from gestion_documental.services.servicio_cuentas import ServicioCuentas

router = APIRouter(prefix="/cuentas", tags=["cuentas"])

Servicio = Annotated[ServicioCuentas, Depends(get_servicio)]
PuedeRadicar = Annotated[Sesion, Depends(requiere_permiso("cuentas.radicar"))]
PuedeConsultar = Annotated[Sesion, Depends(requiere_permiso("cuentas.consultar"))]
PuedeCambiarEstado = Annotated[Sesion, Depends(requiere_permiso("cuentas.cambiar_estado"))]


@router.post("", status_code=status.HTTP_201_CREATED)
def radicar(
    solicitud: SolicitudRadicacion, sesion: PuedeRadicar, servicio: Servicio
) -> CuentaRespuesta:
    comando = RadicarCuenta(id_usuario=sesion.id_usuario, **solicitud.model_dump())
    return CuentaRespuesta.desde_dominio(servicio.radicar(comando))


@router.get("")
def listar_por_estado(
    estado: EstadoCuenta, sesion: PuedeConsultar, servicio: Servicio
) -> list[CuentaRespuesta]:
    return [CuentaRespuesta.desde_dominio(cuenta) for cuenta in servicio.listar_por_estado(estado)]


@router.get("/{numero_radicado}")
def obtener(numero_radicado: str, sesion: PuedeConsultar, servicio: Servicio) -> CuentaRespuesta:
    return CuentaRespuesta.desde_dominio(servicio.obtener(numero_radicado))


@router.post("/{numero_radicado}/estado")
def cambiar_estado(
    numero_radicado: str,
    solicitud: SolicitudCambioEstado,
    sesion: PuedeCambiarEstado,
    servicio: Servicio,
) -> CuentaRespuesta:
    if solicitud.nuevo_estado is EstadoCuenta.PAGADA:
        sesion.exigir_permiso("cuentas.pagar")
    comando = CambiarEstadoCuenta(
        id_usuario=sesion.id_usuario, numero_radicado=numero_radicado, **solicitud.model_dump()
    )
    return CuentaRespuesta.desde_dominio(servicio.cambiar_estado(comando))
