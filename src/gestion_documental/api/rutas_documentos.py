from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.responses import StreamingResponse

from gestion_documental.api.dependencias import ServicioCuentasDep
from gestion_documental.api.esquemas import (
    CuentaRespuesta,
    DocumentoRespuesta,
    SolicitudDocumentoUrl,
)
from gestion_documental.api.seguridad import requiere_permiso
from gestion_documental.domain.archivos import TAMANO_MAXIMO_BYTES
from gestion_documental.domain.enums import OrigenDocumento, TipoDocumento
from gestion_documental.events.comandos import AdjuntarArchivo, AdjuntarDocumento
from gestion_documental.services.servicio_auth import Sesion

router = APIRouter(prefix="/cuentas/{numero_radicado}/documentos", tags=["documentos"])

PuedeAdjuntar = Annotated[Sesion, Depends(requiere_permiso("documentos.adjuntar"))]
PuedeConsultar = Annotated[Sesion, Depends(requiere_permiso("documentos.consultar"))]
PuedeEliminar = Annotated[Sesion, Depends(requiere_permiso("documentos.eliminar"))]


@router.post("", status_code=status.HTTP_201_CREATED)
def subir(
    numero_radicado: str,
    archivo: Annotated[UploadFile, File(description="PDF, JPG o PNG de máximo 10 MB")],
    tipo: Annotated[TipoDocumento, Form()],
    sesion: PuedeAdjuntar,
    servicio: ServicioCuentasDep,
) -> DocumentoRespuesta:
    contenido = archivo.file.read(TAMANO_MAXIMO_BYTES + 1)
    comando = AdjuntarArchivo(
        id_usuario=sesion.id_usuario,
        numero_radicado=numero_radicado,
        nombre_original=archivo.filename or "archivo",
        tipo=tipo,
    )
    return DocumentoRespuesta.desde_dominio(servicio.adjuntar_archivo(comando, contenido))


@router.post("/url", status_code=status.HTTP_201_CREATED)
def adjuntar_url(
    numero_radicado: str,
    solicitud: SolicitudDocumentoUrl,
    sesion: PuedeAdjuntar,
    servicio: ServicioCuentasDep,
) -> CuentaRespuesta:
    comando = AdjuntarDocumento(
        id_usuario=sesion.id_usuario,
        numero_radicado=numero_radicado,
        nombre_original=solicitud.nombre_original,
        ruta_archivo=str(solicitud.url),
        tipo=solicitud.tipo,
        origen=OrigenDocumento.URL,
    )
    return CuentaRespuesta.desde_dominio(servicio.adjuntar(comando))


@router.get("/{id_documento}/descarga")
def descargar(
    numero_radicado: str,
    id_documento: str,
    sesion: PuedeConsultar,
    servicio: ServicioCuentasDep,
) -> StreamingResponse:
    documento, bloques = servicio.descargar(numero_radicado, id_documento)
    return StreamingResponse(
        bloques,
        media_type=documento.tipo_mime,
        headers={
            "Content-Disposition": (
                f"attachment; filename*=UTF-8''{quote(documento.nombre_original)}"
            ),
            "X-Content-SHA256": documento.hash_sha256 or "",
        },
    )


@router.delete("/{id_documento}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    numero_radicado: str,
    id_documento: str,
    sesion: PuedeEliminar,
    servicio: ServicioCuentasDep,
) -> None:
    servicio.eliminar_documento(numero_radicado, id_documento, sesion.id_usuario)
