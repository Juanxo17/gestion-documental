from typing import Annotated

from fastapi import APIRouter, Depends, status

from gestion_documental.api.dependencias import get_servicio
from gestion_documental.api.esquemas import CuentaRespuesta, SolicitudCambioEstado
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.events.comandos import CambiarEstadoCuenta, RadicarCuenta
from gestion_documental.services.servicio_cuentas import ServicioCuentas

router = APIRouter(prefix="/cuentas", tags=["cuentas"])

Servicio = Annotated[ServicioCuentas, Depends(get_servicio)]


@router.post("", status_code=status.HTTP_201_CREATED)
def radicar(comando: RadicarCuenta, servicio: Servicio) -> CuentaRespuesta:
    return CuentaRespuesta.desde_dominio(servicio.radicar(comando))


@router.get("")
def listar_por_estado(estado: EstadoCuenta, servicio: Servicio) -> list[CuentaRespuesta]:
    return [CuentaRespuesta.desde_dominio(cuenta) for cuenta in servicio.listar_por_estado(estado)]


@router.get("/{numero_radicado}")
def obtener(numero_radicado: str, servicio: Servicio) -> CuentaRespuesta:
    return CuentaRespuesta.desde_dominio(servicio.obtener(numero_radicado))


@router.post("/{numero_radicado}/estado")
def cambiar_estado(
    numero_radicado: str, solicitud: SolicitudCambioEstado, servicio: Servicio
) -> CuentaRespuesta:
    comando = CambiarEstadoCuenta(numero_radicado=numero_radicado, **solicitud.model_dump())
    return CuentaRespuesta.desde_dominio(servicio.cambiar_estado(comando))
