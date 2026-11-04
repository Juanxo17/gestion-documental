from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pymongo.errors import ConfigurationError, ServerSelectionTimeoutError

from gestion_documental.api.main import app
from gestion_documental.repositories.conexion import get_db


class BaseDatosFalsa:
    def __init__(self, responde: bool) -> None:
        self.responde = responde

    def command(self, nombre: str) -> dict[str, Any]:
        if not self.responde:
            raise ServerSelectionTimeoutError("sin conexión")
        return {"ok": 1.0}


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_ok_cuando_la_bd_responde(cliente: TestClient) -> None:
    app.dependency_overrides[get_db] = lambda: BaseDatosFalsa(responde=True)

    respuesta = cliente.get("/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "db": "ok"}


def test_health_503_cuando_la_bd_no_responde(cliente: TestClient) -> None:
    app.dependency_overrides[get_db] = lambda: BaseDatosFalsa(responde=False)

    respuesta = cliente.get("/health")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "degraded", "db": "error"}


def test_health_503_cuando_atlas_no_se_puede_resolver(cliente: TestClient) -> None:
    def get_db_sin_dns() -> None:
        raise ConfigurationError("All nameservers failed to answer the query")

    app.dependency_overrides[get_db] = get_db_sin_dns

    respuesta = cliente.get("/health")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "degraded", "db": "error"}
