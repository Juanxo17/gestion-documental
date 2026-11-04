from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from gestion_documental.api.dependencias import Repos, ServicioCuentasDep
from gestion_documental.api.esquemas import EventoRespuesta, GrupoResumen, ResumenRespuesta
from gestion_documental.api.seguridad import requiere_permiso, requiere_rol
from gestion_documental.events.auditoria import FiltroAuditoria
from gestion_documental.services.servicio_auth import Sesion

router_auditoria = APIRouter(prefix="/auditoria", tags=["auditoria"])
router_dashboard = APIRouter(prefix="/dashboard", tags=["dashboard"])

SoloAdministrador = Annotated[Sesion, Depends(requiere_rol("Administrador"))]
PuedeConsultarCuentas = Annotated[Sesion, Depends(requiere_permiso("cuentas.consultar"))]


@router_auditoria.get("")
def buscar_eventos(
    sesion: SoloAdministrador,
    repos: Repos,
    tipo: str | None = None,
    id_usuario: str | None = None,
    desde: datetime | None = None,
    hasta: datetime | None = None,
    limite: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[EventoRespuesta]:
    filtro = FiltroAuditoria(
        tipo=tipo, id_usuario=id_usuario, desde=desde, hasta=hasta, limite=limite
    )
    return [EventoRespuesta.desde_dominio(r) for r in repos.auditoria.buscar(filtro)]


@router_dashboard.get("/resumen")
def resumen(sesion: PuedeConsultarCuentas, servicio: ServicioCuentasDep) -> ResumenRespuesta:
    datos = servicio.resumen()
    return ResumenRespuesta(
        por_estado=[GrupoResumen.desde_dominio(g) for g in datos.por_estado],
        por_contrato=[GrupoResumen.desde_dominio(g) for g in datos.por_contrato],
    )
