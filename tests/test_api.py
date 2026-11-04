from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from gestion_documental.api.dependencias import get_servicio
from gestion_documental.api.main import app
from tests.fabricas import USUARIO_ID, servicio_en_memoria

CUENTA: dict[str, Any] = {
    "id_usuario": USUARIO_ID,
    "numero_radicado": "RAD-API-0001",
    "numero_cuenta": "CUENTA-001",
    "numero_contrato": "CONT-SINT-001",
    "valor_cobro": "1500000.00",
    "concepto_pago": "Honorarios sintéticos",
    "fecha_presentacion": "2026-01-31",
}


@pytest.fixture
def cliente() -> Iterator[TestClient]:
    servicio, _, _ = servicio_en_memoria()
    app.dependency_overrides[get_servicio] = lambda: servicio
    yield TestClient(app)
    app.dependency_overrides.clear()


def cambiar_estado(cliente: TestClient, estado: str, radicado: str = "RAD-API-0001") -> Any:
    return cliente.post(
        f"/cuentas/{radicado}/estado",
        json={"id_usuario": USUARIO_ID, "nuevo_estado": estado, "observacion": "Prueba"},
    )


def test_post_cuentas_radica(cliente: TestClient) -> None:
    respuesta = cliente.post("/cuentas", json=CUENTA)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "RECIBIDA"
    assert cuerpo["valor_cobro"] == "1500000.00"
    assert len(cuerpo["historial"]) == 1


def test_post_cuentas_duplicada_da_409(cliente: TestClient) -> None:
    cliente.post("/cuentas", json=CUENTA)

    respuesta = cliente.post("/cuentas", json=CUENTA)

    assert respuesta.status_code == 409
    assert "RAD-API-0001" in respuesta.json()["detail"]


def test_post_cuentas_contrato_inexistente_da_404(cliente: TestClient) -> None:
    respuesta = cliente.post("/cuentas", json={**CUENTA, "numero_contrato": "CONT-X"})

    assert respuesta.status_code == 404


def test_post_cuentas_datos_invalidos_da_422(cliente: TestClient) -> None:
    respuesta = cliente.post("/cuentas", json={**CUENTA, "valor_cobro": "-5"})

    assert respuesta.status_code == 422


def test_get_cuenta(cliente: TestClient) -> None:
    cliente.post("/cuentas", json=CUENTA)

    respuesta = cliente.get("/cuentas/RAD-API-0001")

    assert respuesta.status_code == 200
    assert respuesta.json()["numero_cuenta"] == "CUENTA-001"


def test_get_cuenta_inexistente_da_404(cliente: TestClient) -> None:
    respuesta = cliente.get("/cuentas/RAD-NO-EXISTE")

    assert respuesta.status_code == 404
    assert "RAD-NO-EXISTE" in respuesta.json()["detail"]


def test_post_estado_valido(cliente: TestClient) -> None:
    cliente.post("/cuentas", json=CUENTA)

    respuesta = cambiar_estado(cliente, "EN_REVISION")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "EN_REVISION"


def test_post_estado_transicion_invalida_da_409(cliente: TestClient) -> None:
    cliente.post("/cuentas", json=CUENTA)

    respuesta = cambiar_estado(cliente, "PAGADA")

    assert respuesta.status_code == 409
    assert "RECIBIDA a PAGADA" in respuesta.json()["detail"]


def test_get_cuentas_por_estado(cliente: TestClient) -> None:
    cliente.post("/cuentas", json=CUENTA)
    cliente.post(
        "/cuentas", json={**CUENTA, "numero_radicado": "RAD-API-0002", "numero_cuenta": "C-2"}
    )
    cambiar_estado(cliente, "EN_REVISION", "RAD-API-0002")

    recibidas = cliente.get("/cuentas", params={"estado": "RECIBIDA"})
    en_revision = cliente.get("/cuentas", params={"estado": "EN_REVISION"})

    assert [c["numero_radicado"] for c in recibidas.json()] == ["RAD-API-0001"]
    assert [c["numero_radicado"] for c in en_revision.json()] == ["RAD-API-0002"]


def test_get_cuentas_estado_desconocido_da_422(cliente: TestClient) -> None:
    assert cliente.get("/cuentas", params={"estado": "PERDIDA"}).status_code == 422
