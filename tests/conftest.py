from collections.abc import Iterator
from typing import Any

import pytest
from pymongo.database import Database

from gestion_documental.config import ConfiguracionError, get_settings
from gestion_documental.repositories.conexion import get_client
from gestion_documental.repositories.indices import crear_indices


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
