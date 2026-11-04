from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from gestion_documental.api.dependencias import ServicioCuentasDep
from gestion_documental.api.esquemas import (
    CambioRespuesta,
    CuentaRespuesta,
    PaginaCuentasRespuesta,
    SolicitudCambioEstado,
    SolicitudEdicionCuenta,
    SolicitudObservacion,
    SolicitudRadicacion,
)
from gestion_documental.api.seguridad import requiere_permiso
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.events.comandos import CambiarEstadoCuenta, EditarCuenta, RadicarCuenta
from gestion_documental.services.servicio_auth import Sesion

router = APIRouter(prefix="/cuentas", tags=["cuentas"])

PuedeRadicar = Annotated[Sesion, Depends(requiere_permiso("cuentas.radicar"))]
PuedeConsultar = Annotated[Sesion, Depends(requiere_permiso("cuentas.consultar"))]
PuedeEditar = Annotated[Sesion, Depends(requiere_permiso("cuentas.editar"))]
PuedeCambiarEstado = Annotated[Sesion, Depends(requiere_permiso("cuentas.cambiar_estado"))]
PuedePagar = Annotated[Sesion, Depends(requiere_permiso("cuentas.pagar"))]


@router.post("", status_code=status.HTTP_201_CREATED)
def radicar(
    solicitud: SolicitudRadicacion, sesion: PuedeRadicar, servicio: ServicioCuentasDep
) -> CuentaRespuesta:
    comando = RadicarCuenta(id_usuario=sesion.id_usuario, **solicitud.model_dump())
    return CuentaRespuesta.desde_dominio(servicio.radicar(comando))


@router.get("")
def buscar(
    sesion: PuedeConsultar,
    servicio: ServicioCuentasDep,
    estado: EstadoCuenta | None = None,
    numero_contrato: str | None = None,
    nit_contratista: str | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamano: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginaCuentasRespuesta:
    resultado = servicio.buscar(
        estado=estado,
        numero_contrato=numero_contrato,
        nit_contratista=nit_contratista,
        desde=desde,
        hasta=hasta,
        pagina=pagina,
        tamano=tamano,
    )
    return PaginaCuentasRespuesta(
        total=resultado.total,
        pagina=resultado.pagina,
        tamano=resultado.tamano,
        items=[CuentaRespuesta.desde_dominio(cuenta) for cuenta in resultado.items],
    )


@router.get("/{numero_radicado}")
def obtener(
    numero_radicado: str, sesion: PuedeConsultar, servicio: ServicioCuentasDep
) -> CuentaRespuesta:
    return CuentaRespuesta.desde_dominio(servicio.obtener(numero_radicado))


@router.get("/{numero_radicado}/historial")
def historial(
    numero_radicado: str, sesion: PuedeConsultar, servicio: ServicioCuentasDep
) -> list[CambioRespuesta]:
    return [CambioRespuesta.desde_dominio(c) for c in servicio.historial(numero_radicado)]


@router.patch("/{numero_radicado}")
def editar(
    numero_radicado: str,
    solicitud: SolicitudEdicionCuenta,
    sesion: PuedeEditar,
    servicio: ServicioCuentasDep,
) -> CuentaRespuesta:
    comando = EditarCuenta(
        id_usuario=sesion.id_usuario,
        numero_radicado=numero_radicado,
        **solicitud.model_dump(),
    )
    return CuentaRespuesta.desde_dominio(servicio.editar(comando))


@router.post("/{numero_radicado}/estado")
def cambiar_estado(
    numero_radicado: str,
    solicitud: SolicitudCambioEstado,
    sesion: PuedeCambiarEstado,
    servicio: ServicioCuentasDep,
) -> CuentaRespuesta:
    if solicitud.nuevo_estado is EstadoCuenta.PAGADA:
        sesion.exigir_permiso("cuentas.pagar")
    comando = CambiarEstadoCuenta(
        id_usuario=sesion.id_usuario, numero_radicado=numero_radicado, **solicitud.model_dump()
    )
    return CuentaRespuesta.desde_dominio(servicio.cambiar_estado(comando))


@router.post("/{numero_radicado}/anular")
def anular(
    numero_radicado: str,
    solicitud: SolicitudObservacion,
    sesion: PuedeCambiarEstado,
    servicio: ServicioCuentasDep,
) -> CuentaRespuesta:
    cuenta = servicio.anular(numero_radicado, sesion.id_usuario, solicitud.observacion)
    return CuentaRespuesta.desde_dominio(cuenta)


@router.post("/{numero_radicado}/pagar")
def pagar(
    numero_radicado: str,
    solicitud: SolicitudObservacion,
    sesion: PuedePagar,
    servicio: ServicioCuentasDep,
) -> CuentaRespuesta:
    cuenta = servicio.pagar(numero_radicado, sesion.id_usuario, solicitud.observacion)
    return CuentaRespuesta.desde_dominio(cuenta)
