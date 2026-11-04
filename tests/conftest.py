from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pymongo.database import Database

from gestion_documental.api.dependencias import get_hasher, get_repositorios
from gestion_documental.api.main import app
from gestion_documental.config import (
    ConfiguracionAuth,
    ConfiguracionError,
    get_config_auth,
    get_settings,
)
from gestion_documental.repositories.conexion import get_client
from gestion_documental.repositories.indices import crear_indices
from tests.cliente_api import ClienteApi
from tests.fabricas import HASHER_RAPIDO, SECRETO_PRUEBAS, escenario


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
    datos = escenario()
    app.dependency_overrides[get_repositorios] = lambda: datos.repos
    app.dependency_overrides[get_hasher] = lambda: HASHER_RAPIDO
    app.dependency_overrides[get_config_auth] = lambda: ConfiguracionAuth(
        jwt_secret=SECRETO_PRUEBAS, jwt_minutos=30
    )
    yield ClienteApi(TestClient(app), datos)
    app.dependency_overrides.clear()
