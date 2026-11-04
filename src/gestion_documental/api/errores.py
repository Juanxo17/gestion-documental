from bson.errors import InvalidId
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from pymongo.errors import ConfigurationError, ConnectionFailure
from starlette.exceptions import HTTPException

from gestion_documental.domain.errores import (
    AccesoDenegadoError,
    ArchivoDemasiadoGrandeError,
    ArchivoInvalidoError,
    ErrorDominio,
    NoEncontradoError,
    TransicionInvalidaError,
    UsuarioBloqueadoError,
    UsuarioInactivoError,
)
from gestion_documental.repositories.base import RegistroDuplicadoError
from gestion_documental.services.servicio_auth import (
    CambioContrasenaRequeridoError,
    CredencialesInvalidasError,
    PermisoDenegadoError,
)
from gestion_documental.services.servicio_cuentas import IntegridadArchivoError

RUTA_SALUD = "/health"

ERRORES: dict[type[Exception], tuple[int, str]] = {
    ErrorDominio: (400, "ERROR_DE_NEGOCIO"),
    ArchivoInvalidoError: (400, "ARCHIVO_INVALIDO"),
    InvalidId: (400, "IDENTIFICADOR_INVALIDO"),
    CredencialesInvalidasError: (401, "NO_AUTENTICADO"),
    AccesoDenegadoError: (403, "ACCESO_DENEGADO"),
    PermisoDenegadoError: (403, "PERMISO_DENEGADO"),
    UsuarioInactivoError: (403, "USUARIO_INACTIVO"),
    UsuarioBloqueadoError: (403, "USUARIO_BLOQUEADO"),
    CambioContrasenaRequeridoError: (403, "CAMBIO_DE_CONTRASENA_REQUERIDO"),
    NoEncontradoError: (404, "NO_ENCONTRADO"),
    RegistroDuplicadoError: (409, "DUPLICADO"),
    TransicionInvalidaError: (409, "TRANSICION_INVALIDA"),
    IntegridadArchivoError: (409, "INTEGRIDAD_DEL_ARCHIVO"),
    ArchivoDemasiadoGrandeError: (413, "ARCHIVO_DEMASIADO_GRANDE"),
    ConfigurationError: (503, "BD_NO_DISPONIBLE"),
    ConnectionFailure: (503, "BD_NO_DISPONIBLE"),
}

CODIGOS_HTTP = {
    401: "NO_AUTENTICADO",
    403: "ACCESO_DENEGADO",
    404: "NO_ENCONTRADO",
    405: "METODO_NO_PERMITIDO",
}


def respuesta_error(
    estado: int, codigo: str, detalle: str, cabeceras: dict[str, str] | None = None
) -> JSONResponse:
    if estado == 401:
        cabeceras = {**(cabeceras or {}), "WWW-Authenticate": "Bearer"}
    return JSONResponse(
        status_code=estado, content={"error": codigo, "detalle": detalle}, headers=cabeceras
    )


def describir_validacion(errores: list[dict[str, object]]) -> str:
    partes = []
    for error in errores:
        ubicacion = ".".join(str(parte) for parte in error.get("loc", ()) if parte != "body")  # type: ignore[attr-defined]
        partes.append(f"{ubicacion}: {error.get('msg')}" if ubicacion else str(error.get("msg")))
    return "; ".join(partes)


async def manejar_conocido(request: Request, exc: Exception) -> JSONResponse:
    estado, codigo = next(ERRORES[tipo] for tipo in type(exc).__mro__ if tipo in ERRORES)
    if estado == 503 and request.url.path == RUTA_SALUD:
        return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})
    return respuesta_error(estado, codigo, str(exc))


async def manejar_validacion(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError | ValidationError)
    return respuesta_error(422, "VALIDACION", describir_validacion(list(exc.errors())))  # type: ignore[arg-type]


async def manejar_http(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, HTTPException)
    codigo = CODIGOS_HTTP.get(exc.status_code, f"HTTP_{exc.status_code}")
    return respuesta_error(exc.status_code, codigo, str(exc.detail), dict(exc.headers or {}))


def registrar_manejadores(app: FastAPI) -> None:
    for tipo in ERRORES:
        app.add_exception_handler(tipo, manejar_conocido)
    app.add_exception_handler(RequestValidationError, manejar_validacion)
    app.add_exception_handler(ValidationError, manejar_validacion)
    app.add_exception_handler(HTTPException, manejar_http)
