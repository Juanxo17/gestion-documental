from typing import Any

from httpx2 import Response

from tests.cliente_api import ClienteApi

RADICADOR = "radicador@example.com"
REVISOR = "revisor@example.com"
ADMIN = "administrador@example.com"

CUENTA: dict[str, Any] = {
    "numero_radicado": "RAD-API-0001",
    "numero_cuenta": "CUENTA-001",
    "numero_contrato": "CONT-SINT-001",
    "valor_cobro": "1500000.00",
    "concepto_pago": "Honorarios sintéticos",
    "fecha_presentacion": "2026-01-31",
}


def radicar(api: ClienteApi, **cambios: Any) -> Response:
    return api.http.post("/cuentas", json={**CUENTA, **cambios}, headers=api.cabeceras(RADICADOR))


def cambiar_estado(
    api: ClienteApi, estado: str, radicado: str = "RAD-API-0001", correo: str = REVISOR
) -> Response:
    return api.http.post(
        f"/cuentas/{radicado}/estado",
        json={"nuevo_estado": estado, "observacion": "Prueba"},
        headers=api.cabeceras(correo),
    )


def test_post_cuentas_radica_con_el_usuario_del_token(api: ClienteApi) -> None:
    respuesta = radicar(api)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    radicador = api.usuarios.obtener_por_correo(RADICADOR)
    assert radicador is not None
    assert cuerpo["estado"] == "RECIBIDA"
    assert cuerpo["valor_cobro"] == "1500000.00"
    assert cuerpo["historial"][0]["id_usuario"] == radicador.id


def test_post_cuentas_rechaza_id_usuario_en_el_cuerpo(api: ClienteApi) -> None:
    assert radicar(api, id_usuario="otro").status_code == 422


def test_post_cuentas_duplicada_da_409(api: ClienteApi) -> None:
    radicar(api)

    respuesta = radicar(api)

    assert respuesta.status_code == 409
    assert "RAD-API-0001" in respuesta.json()["detail"]


def test_post_cuentas_contrato_inexistente_da_404(api: ClienteApi) -> None:
    assert radicar(api, numero_contrato="CONT-X").status_code == 404


def test_post_cuentas_datos_invalidos_da_422(api: ClienteApi) -> None:
    assert radicar(api, valor_cobro="-5").status_code == 422


def test_get_cuenta(api: ClienteApi) -> None:
    radicar(api)

    respuesta = api.http.get("/cuentas/RAD-API-0001", headers=api.cabeceras(REVISOR))

    assert respuesta.status_code == 200
    assert respuesta.json()["numero_cuenta"] == "CUENTA-001"


def test_get_cuenta_inexistente_da_404(api: ClienteApi) -> None:
    respuesta = api.http.get("/cuentas/RAD-NO-EXISTE", headers=api.cabeceras(REVISOR))

    assert respuesta.status_code == 404
    assert "RAD-NO-EXISTE" in respuesta.json()["detail"]


def test_post_estado_valido(api: ClienteApi) -> None:
    radicar(api)

    respuesta = cambiar_estado(api, "EN_REVISION")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "EN_REVISION"


def test_post_estado_transicion_invalida_da_409(api: ClienteApi) -> None:
    radicar(api)

    respuesta = cambiar_estado(api, "APROBADA")

    assert respuesta.status_code == 409
    assert "RECIBIDA a APROBADA" in respuesta.json()["detail"]


def test_get_cuentas_por_estado(api: ClienteApi) -> None:
    radicar(api)
    radicar(api, numero_radicado="RAD-API-0002", numero_cuenta="C-2")
    cambiar_estado(api, "EN_REVISION", "RAD-API-0002")
    cabeceras = api.cabeceras(REVISOR)

    recibidas = api.http.get("/cuentas", params={"estado": "RECIBIDA"}, headers=cabeceras)
    en_revision = api.http.get("/cuentas", params={"estado": "EN_REVISION"}, headers=cabeceras)

    assert [c["numero_radicado"] for c in recibidas.json()] == ["RAD-API-0001"]
    assert [c["numero_radicado"] for c in en_revision.json()] == ["RAD-API-0002"]


def test_get_cuentas_estado_desconocido_da_422(api: ClienteApi) -> None:
    respuesta = api.http.get(
        "/cuentas", params={"estado": "PERDIDA"}, headers=api.cabeceras(REVISOR)
    )

    assert respuesta.status_code == 422


def test_pagada_exige_ademas_cuentas_pagar(api: ClienteApi) -> None:
    radicar(api)
    cambiar_estado(api, "EN_REVISION")
    cambiar_estado(api, "APROBADA")

    sin_permiso = cambiar_estado(api, "PAGADA", correo=REVISOR)
    con_permiso = cambiar_estado(api, "PAGADA", correo=ADMIN)

    assert sin_permiso.status_code == 403
    assert "cuentas.pagar" in sin_permiso.json()["detail"]
    assert con_permiso.status_code == 200
    assert con_permiso.json()["estado"] == "PAGADA"
