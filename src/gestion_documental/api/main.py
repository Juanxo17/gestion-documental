from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from pymongo.database import Database

from gestion_documental.repositories.conexion import get_db, ping

app = FastAPI(title="Gestión Documental")


@app.get("/health")
def health(db: Annotated[Database[dict[str, Any]], Depends(get_db)]) -> JSONResponse:
    if ping(db):
        return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
    return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})
