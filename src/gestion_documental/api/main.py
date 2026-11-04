from typing import Annotated, Any

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pymongo.database import Database
from pymongo.errors import ConfigurationError, ConnectionFailure

from gestion_documental.repositories.conexion import get_db, ping

BD_NO_DISPONIBLE = {"status": "degraded", "db": "error"}

app = FastAPI(title="Gestión Documental")


async def responder_bd_no_disponible(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=503, content=BD_NO_DISPONIBLE)


app.add_exception_handler(ConfigurationError, responder_bd_no_disponible)
app.add_exception_handler(ConnectionFailure, responder_bd_no_disponible)


@app.get("/health")
def health(db: Annotated[Database[dict[str, Any]], Depends(get_db)]) -> JSONResponse:
    if ping(db):
        return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
    return JSONResponse(status_code=503, content=BD_NO_DISPONIBLE)
