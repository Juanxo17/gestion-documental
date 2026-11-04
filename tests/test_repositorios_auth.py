from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from gestion_documental.repositories.base import (
    RegistroDuplicadoError,
    RepositorioRoles,
    RepositorioUsuarios,
)
from gestion_documental.repositories.mapeo import COLECCION_ROLES, rol_a_dict
from gestion_documental.repositories.memoria import (
    RepositorioRolesEnMemoria,
    RepositorioUsuariosEnMemoria,
)
from gestion_documental.repositories.mongo import RepositorioRolesMongo, RepositorioUsuariosMongo
from tests.fabricas import roles_sinteticos, usuarios_sinteticos

MOMENTO = datetime(2026, 1, 31, 9, 0, 0, 500000, tzinfo=UTC)


@dataclass
class Repositorios:
    usuarios: RepositorioUsuarios
    roles: RepositorioRoles


@pytest.fixture(params=["memoria", pytest.param("mongo", marks=pytest.mark.integracion)])
def repos(request: pytest.FixtureRequest) -> Repositorios:
    roles = roles_sinteticos()
    if request.param == "memoria":
        return Repositorios(RepositorioUsuariosEnMemoria(), RepositorioRolesEnMemoria(roles))
    db = request.getfixturevalue("db_pruebas")
    db[COLECCION_ROLES].insert_many(rol_a_dict(rol) for rol in roles)
    return Repositorios(RepositorioUsuariosMongo(db), RepositorioRolesMongo(db))


def test_guardar_y_obtener_usuario_por_id_y_correo(repos: Repositorios) -> None:
    usuario = usuarios_sinteticos(roles_sinteticos())[0]
    usuario.fecha_registro = MOMENTO
    usuario.bloqueado_hasta = MOMENTO

    repos.usuarios.guardar(usuario)

    assert usuario.id is not None
    assert repos.usuarios.obtener_por_id(usuario.id) == usuario
    assert repos.usuarios.obtener_por_correo(usuario.correo) == usuario


def test_usuario_inexistente(repos: Repositorios) -> None:
    assert repos.usuarios.obtener_por_id("64c000000000000000000099") is None
    assert repos.usuarios.obtener_por_id("no-es-un-id") is None
    assert repos.usuarios.obtener_por_correo("nadie@example.com") is None


def test_guardar_dos_veces_actualiza(repos: Repositorios) -> None:
    usuario = usuarios_sinteticos(roles_sinteticos())[0]
    repos.usuarios.guardar(usuario)
    usuario.registrar_login_fallido(MOMENTO)

    repos.usuarios.guardar(usuario)

    assert usuario.id is not None
    recuperado = repos.usuarios.obtener_por_id(usuario.id)
    assert recuperado is not None
    assert recuperado.intentos_fallidos == 1


def test_correo_duplicado(repos: Repositorios) -> None:
    primero, segundo = usuarios_sinteticos(roles_sinteticos())[:2]
    repos.usuarios.guardar(primero)
    segundo.correo = primero.correo

    with pytest.raises(RegistroDuplicadoError):
        repos.usuarios.guardar(segundo)


def test_obtener_rol_con_permisos(repos: Repositorios) -> None:
    consulta = next(rol for rol in roles_sinteticos() if rol.nombre == "Consulta")
    assert consulta.id is not None

    recuperado = repos.roles.obtener_por_id(consulta.id)

    assert recuperado == consulta
    assert recuperado is not None
    assert recuperado.tiene_permiso("cuentas.consultar")
    assert repos.roles.obtener_por_id("64c000000000000000000099") is None
