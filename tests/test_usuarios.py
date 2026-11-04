from datetime import UTC, datetime, timedelta

import pytest

from gestion_documental.domain.errores import UsuarioBloqueadoError, UsuarioInactivoError
from gestion_documental.domain.usuarios import DURACION_BLOQUEO, MAXIMO_INTENTOS, Rol, Usuario

AHORA = datetime(2026, 1, 31, 10, 0, tzinfo=UTC)


def usuario(**cambios: object) -> Usuario:
    datos: dict[str, object] = {
        "nombre": "Ana",
        "apellido": "Sintética",
        "correo": "ana@example.com",
        "id_rol": "rol-1",
        "cargo": "Auxiliar",
        "contrasena_hash": "hash",
        **cambios,
    }
    return Usuario(**datos)  # type: ignore[arg-type]


def test_cinco_fallos_bloquean_quince_minutos() -> None:
    cuenta = usuario()

    for _ in range(MAXIMO_INTENTOS - 1):
        cuenta.registrar_login_fallido(AHORA)
    assert not cuenta.esta_bloqueado(AHORA)

    cuenta.registrar_login_fallido(AHORA)

    assert cuenta.bloqueado_hasta == AHORA + DURACION_BLOQUEO
    with pytest.raises(UsuarioBloqueadoError, match="bloqueado"):
        cuenta.verificar_bloqueo(AHORA + timedelta(minutes=14))
    cuenta.verificar_bloqueo(AHORA + timedelta(minutes=15))


def test_fallo_despues_de_vencer_el_bloqueo_empieza_de_cero() -> None:
    cuenta = usuario(intentos_fallidos=5, bloqueado_hasta=AHORA)

    cuenta.registrar_login_fallido(AHORA + timedelta(minutes=1))

    assert cuenta.intentos_fallidos == 1
    assert cuenta.bloqueado_hasta is None


def test_login_exitoso_reinicia_intentos_y_actualiza_acceso() -> None:
    cuenta = usuario(intentos_fallidos=3)

    cuenta.registrar_login_exitoso(AHORA)

    assert cuenta.intentos_fallidos == 0
    assert cuenta.ultimo_acceso == AHORA


def test_usuario_inactivo_no_entra() -> None:
    with pytest.raises(UsuarioInactivoError):
        usuario(activo=False).verificar_activo()


def test_cambiar_contrasena_quita_la_obligacion() -> None:
    cuenta = usuario(debe_cambiar_contrasena=True)

    cuenta.cambiar_contrasena("nuevo-hash")

    assert cuenta.contrasena_hash == "nuevo-hash"
    assert not cuenta.debe_cambiar_contrasena


def test_rol_inactivo_no_concede_permisos() -> None:
    rol = Rol(nombre="Consulta", descripcion="Lectura", permisos=frozenset({"cuentas.consultar"}))

    assert rol.tiene_permiso("cuentas.consultar")
    assert not rol.tiene_permiso("cuentas.radicar")
    rol.activo = False
    assert not rol.tiene_permiso("cuentas.consultar")
