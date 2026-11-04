from typing import Annotated, Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.database import Database

from gestion_documental.api.errores import registrar_manejadores
from gestion_documental.api.rutas_auth import router as rutas_auth
from gestion_documental.api.rutas_consultas import router_auditoria, router_dashboard
from gestion_documental.api.rutas_contratistas import router as rutas_contratistas
from gestion_documental.api.rutas_contratos import router as rutas_contratos
from gestion_documental.api.rutas_cuentas import router as rutas_cuentas
from gestion_documental.api.rutas_documentos import router as rutas_documentos
from gestion_documental.api.rutas_usuarios import router as rutas_usuarios
from gestion_documental.config import ConfiguracionApi, cargar
from gestion_documental.repositories.conexion import get_db, ping

ETIQUETAS = [
    {"name": "auth", "description": "Inicio de sesión, usuario actual y cambio de contraseña"},
    {"name": "usuarios", "description": "Administración de usuarios (usuarios.gestionar)"},
    {"name": "contratistas", "description": "Personas naturales y jurídicas"},
    {"name": "contratos", "description": "Contratos, vigencia y estados"},
    {"name": "cuentas", "description": "Radicación y trámite de cuentas de cobro"},
    {"name": "documentos", "description": "Adjuntos en GridFS o por URL"},
    {"name": "auditoria", "description": "Eventos persistidos (solo Administrador)"},
    {"name": "dashboard", "description": "Agregaciones por estado y contrato"},
    {"name": "sistema", "description": "Salud de la API y de la base de datos"},
]

app = FastAPI(title="Gestión Documental", openapi_tags=ETIQUETAS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cargar(ConfiguracionApi).origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
registrar_manejadores(app)
for router in (
    rutas_auth,
    rutas_usuarios,
    rutas_contratistas,
    rutas_contratos,
    rutas_cuentas,
    rutas_documentos,
    router_auditoria,
    router_dashboard,
):
    app.include_router(router)


@app.get("/health", tags=["sistema"])
def health(db: Annotated[Database[dict[str, Any]], Depends(get_db)]) -> JSONResponse:
    if ping(db):
        return JSONResponse(status_code=200, content={"status": "ok", "db": "ok"})
    return JSONResponse(status_code=503, content={"status": "degraded", "db": "error"})
