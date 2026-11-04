from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pymongo.database import Database

from gestion_documental.api.dependencias import get_servicio
from gestion_documental.api.main import app
from gestion_documental.api.seguridad import get_servicio_auth
from gestion_documental.config import ConfiguracionError, get_settings
from gestion_documental.repositories.conexion import get_client
from gestion_documental.repositories.indices import crear_indices
from tests.cliente_api import ClienteApi
from tests.fabricas import servicio_auth_en_memoria, servicio_en_memoria


@pytest.fixture
def db_pruebas() -> Iterator[Database[dict[str, Any]]]:
    try:
        nombre = f"{get_settings().mongo_db}_pruebas"
    except ConfiguracionError:
        pytest.skip("Sin .env: se omiten las pruebas contra MongoDB")
    cliente = get_client()
    cliente.drop_database(nombre)
    db = cliente[nombre]
    crear_indices(db)
    yield db
    cliente.drop_database(nombre)


@pytest.fixture
def api() -> Iterator[ClienteApi]:
    servicio, _, _ = servicio_en_memoria()
    servicio_auth, usuarios = servicio_auth_en_memoria()
    app.dependency_overrides[get_servicio] = lambda: servicio
    app.dependency_overrides[get_servicio_auth] = lambda: servicio_auth
    yield ClienteApi(TestClient(app), usuarios)
    app.dependency_overrides.clear()
