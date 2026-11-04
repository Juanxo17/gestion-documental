from typing import Annotated, Any

from bson.errors import InvalidId
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.database import Database
from pymongo.errors import ConfigurationError, ConnectionFailure

from gestion_documental.api.rutas_cuentas import router as rutas_cuentas
from gestion_documental.domain.errores import ErrorDominio, TransicionInvalidaError
from gestion_documental.repositories.base import RegistroDuplicadoError
from gestion_documental.repositories.conexion import get_db, ping
from gestion_documental.services.servicio_cuentas import NoEncontradoError

BD_NO_DISPONIBLE = {"status": "degraded", "db": "error"}

ESTADOS_POR_ERROR: dict[type[Exception], int] = {
    ErrorDominio: 400,
    InvalidId: 400,
    NoEncontradoError: 404,
    RegistroDuplicadoError: 409,
    TransicionInvalidaError: 409,
}

app = FastAPI(title="Gestión Documental")
app.include_router(rutas_cuentas)


async def responder_bd_no_disponible(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content=BD_NO_DISPONIBLE)


async def responder_error_conocido(request: Request, exc: Exception) -> JSONResponse:
    codigo = next(
        ESTADOS_POR_ERROR[tipo] for tipo in type(exc).__mro__ if tipo in ESTADOS_POR_ERROR
    )
    return JSONResponse(status_code=codigo, content={"detail": str(exc)})


app.add_exception_handler(ConfigurationError, responder_bd_no_disponible)
app.add_exception_handler(ConnectionFailure, responder_bd_no_disponible)
for tipo_error in ESTADOS_POR_ERROR:
    app.add_exception_handler(tipo_error, responder_error_conocido)


@app.get("/health")
def health(db: Annotated[Database[dict[str, Any]], Depends(get_db)]) -> JSONResponse:
    if ping(db):
        return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
    return JSONResponse(status_code=503, content=BD_NO_DISPONIBLE)
