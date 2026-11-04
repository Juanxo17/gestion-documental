from datetime import UTC, datetime, timedelta

import pytest

from gestion_documental.domain.errores import UsuarioBloqueadoError, UsuarioInactivoError
from gestion_documental.services.servicio_auth import CredencialesInvalidasError
from tests.cliente_api import ClienteApi
from tests.fabricas import CONTRASENA, servicio_auth_en_memoria

CONSULTA = "consulta@example.com"
RADICADOR = "radicador@example.com"
NUEVO = "nuevo@example.com"


class RelojFalso:
    def __init__(self) -> None:
        self.ahora = datetime.now(UTC)

    def __call__(self) -> datetime:
        return self.ahora


def test_login_correcto_devuelve_token(api: ClienteApi) -> None:
    respuesta = api.login(RADICADOR)

    assert respuesta.status_code == 200
    assert respuesta.json()["token_type"] == "bearer"
    assert respuesta.json()["access_token"].count(".") == 2


def test_login_incorrecto_da_401_y_cuenta_el_intento(api: ClienteApi) -> None:
    respuesta = api.login(RADICADOR, "equivocada")

    assert respuesta.status_code == 401
    assert respuesta.headers["WWW-Authenticate"] == "Bearer"
    usuario = api.usuarios.obtener_por_correo(RADICADOR)
    assert usuario is not None
    assert usuario.intentos_fallidos == 1


def test_correo_inexistente_da_el_mismo_mensaje(api: ClienteApi) -> None:
    inexistente = api.login("nadie@example.com")
    equivocada = api.login(RADICADOR, "equivocada")

    assert inexistente.status_code == equivocada.status_code == 401
    assert inexistente.json() == equivocada.json()


def test_cinco_fallos_bloquean_aunque_luego_acierte(api: ClienteApi) -> None:
    for _ in range(5):
        assert api.login(RADICADOR, "equivocada").status_code == 401

    respuesta = api.login(RADICADOR)

    assert respuesta.status_code == 403
    assert "bloqueado" in respuesta.json()["detail"]


def test_bloqueo_vence_a_los_quince_minutos() -> None:
    reloj = RelojFalso()
    servicio, _ = servicio_auth_en_memoria(reloj)
    for _ in range(5):
        with pytest.raises(CredencialesInvalidasError):
            servicio.login(RADICADOR, "equivocada")

    reloj.ahora += timedelta(minutes=14)
    with pytest.raises(UsuarioBloqueadoError):
        servicio.login(RADICADOR, CONTRASENA)

    reloj.ahora += timedelta(minutes=1)
    assert servicio.login(RADICADOR, CONTRASENA)


def test_login_exitoso_reinicia_intentos_y_registra_acceso() -> None:
    servicio, usuarios = servicio_auth_en_memoria()
    with pytest.raises(CredencialesInvalidasError):
        servicio.login(RADICADOR, "equivocada")

    servicio.login(RADICADOR, CONTRASENA)

    usuario = usuarios.obtener_por_correo(RADICADOR)
    assert usuario is not None
    assert usuario.intentos_fallidos == 0
    assert usuario.ultimo_acceso is not None


def test_usuario_inactivo_no_entra(api: ClienteApi) -> None:
    respuesta = api.login("inactivo@example.com")

    assert respuesta.status_code == 403
    assert "inactivo" in respuesta.json()["detail"]


def test_usuario_inactivo_en_servicio() -> None:
    servicio, _ = servicio_auth_en_memoria()

    with pytest.raises(UsuarioInactivoError):
        servicio.login("inactivo@example.com", CONTRASENA)


def test_sin_token_da_401(api: ClienteApi) -> None:
    assert api.http.get("/cuentas", params={"estado": "RECIBIDA"}).status_code == 401
    assert api.http.get("/auth/me").status_code == 401


def test_token_alterado_da_401(api: ClienteApi) -> None:
    cabeceras = api.cabeceras(RADICADOR)
    cabeceras["Authorization"] += "x"

    assert api.http.get("/auth/me", headers=cabeceras).status_code == 401


def test_me_devuelve_usuario_rol_y_permisos(api: ClienteApi) -> None:
    respuesta = api.http.get("/auth/me", headers=api.cabeceras(CONSULTA))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["correo"] == CONSULTA
    assert cuerpo["rol"] == "Consulta"
    assert cuerpo["permisos"] == [
        "contratistas.consultar",
        "contratos.consultar",
        "cuentas.consultar",
        "documentos.consultar",
    ]


def test_rol_consulta_no_puede_radicar(api: ClienteApi) -> None:
    respuesta = api.http.post(
        "/cuentas",
        json={
            "numero_radicado": "RAD-1",
            "numero_cuenta": "C-1",
            "numero_contrato": "CONT-SINT-001",
            "valor_cobro": "10.00",
            "concepto_pago": "Prueba",
            "fecha_presentacion": "2026-01-31",
        },
        headers=api.cabeceras(CONSULTA),
    )

    assert respuesta.status_code == 403
    assert "cuentas.radicar" in respuesta.json()["detail"]


def test_permiso_faltante_da_403(api: ClienteApi) -> None:
    respuesta = api.http.post(
        "/cuentas/RAD-1/estado",
        json={"nuevo_estado": "EN_REVISION"},
        headers=api.cabeceras(RADICADOR),
    )

    assert respuesta.status_code == 403
    assert "cuentas.cambiar_estado" in respuesta.json()["detail"]


def test_cambio_obligatorio_de_contrasena(api: ClienteApi) -> None:
    cabeceras = api.cabeceras(NUEVO)

    bloqueado = api.http.get("/cuentas", params={"estado": "RECIBIDA"}, headers=cabeceras)
    me = api.http.get("/auth/me", headers=cabeceras)
    cambio = api.http.post(
        "/auth/cambiar-contrasena",
        json={"contrasena_actual": CONTRASENA, "contrasena_nueva": "NuevaClave2026*"},
        headers=cabeceras,
    )
    permitido = api.http.get("/cuentas", params={"estado": "RECIBIDA"}, headers=cabeceras)

    assert bloqueado.status_code == 403
    assert "cambiar su contraseña" in bloqueado.json()["detail"]
    assert me.status_code == 200
    assert me.json()["debe_cambiar_contrasena"] is True
    assert cambio.status_code == 204
    assert permitido.status_code == 200
    assert api.login(NUEVO, "NuevaClave2026*").status_code == 200
    assert api.login(NUEVO, CONTRASENA).status_code == 401


@pytest.mark.parametrize(
    ("actual", "nueva", "mensaje"),
    [
        ("equivocada", "NuevaClave2026*", "actual no es correcta"),
        (CONTRASENA, "corta", "al menos 8"),
        (CONTRASENA, CONTRASENA, "distinta"),
    ],
)
def test_cambio_de_contrasena_invalido_da_400(
    api: ClienteApi, actual: str, nueva: str, mensaje: str
) -> None:
    respuesta = api.http.post(
        "/auth/cambiar-contrasena",
        json={"contrasena_actual": actual, "contrasena_nueva": nueva},
        headers=api.cabeceras(NUEVO),
    )

    assert respuesta.status_code == 400
    assert mensaje in respuesta.json()["detail"]
