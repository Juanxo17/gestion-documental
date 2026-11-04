from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from bson import ObjectId

from gestion_documental.datos_sinteticos import pdf_sintetico
from gestion_documental.domain.contratistas import PersonaJuridica, PersonaNatural
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta
from gestion_documental.domain.errores import NoEncontradoError
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.events.auditoria import FiltroAuditoria, RegistroEvento
from gestion_documental.repositories.base import (
    FiltroCuentas,
    RegistroDuplicadoError,
    Repositorios,
    ResumenGrupo,
)
from gestion_documental.repositories.mapeo import COLECCION_ROLES, rol_a_dict
from gestion_documental.repositories.memoria import repositorios_en_memoria
from gestion_documental.repositories.mongo import repositorios_mongo
from tests.fabricas import roles_sinteticos, usuarios_sinteticos

CONTRATO_A = str(ObjectId())
CONTRATO_B = str(ObjectId())
USUARIO = str(ObjectId())
MOMENTO = datetime(2026, 3, 1, 12, 0, 0, 250000, tzinfo=UTC)


@pytest.fixture(params=["memoria", pytest.param("mongo", marks=pytest.mark.integracion)])
def repos(request: pytest.FixtureRequest) -> Repositorios:
    roles = roles_sinteticos()
    if request.param == "memoria":
        return repositorios_en_memoria(roles=roles)
    db = request.getfixturevalue("db_pruebas")
    db[COLECCION_ROLES].insert_many(rol_a_dict(rol) for rol in roles)
    return repositorios_mongo(db)


def cuenta(radicado: str, contrato: str = CONTRATO_A, **cambios: Any) -> CuentaCobro:
    datos: dict[str, Any] = {
        "numero_radicado": radicado,
        "numero_cuenta": f"C-{radicado}",
        "id_contrato": contrato,
        "valor_cobro": ValorMonetario(Decimal("100.00")),
        "concepto_pago": "Concepto sintético",
        "fecha_presentacion": date(2026, 1, 15),
        "id_usuario": USUARIO,
        **cambios,
    }
    return CuentaCobro(**datos)


def contrato(numero: str, contratista: str | None = None) -> Contrato:
    return Contrato(
        numero_contrato=numero,
        id_contratista=contratista or str(ObjectId()),
        objeto_contrato="Objeto",
        valor_total=ValorMonetario(Decimal("1000.00")),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        id_supervisor=str(ObjectId()),
    )


def test_buscar_cuentas_filtra_y_pagina(repos: Repositorios) -> None:
    for indice in range(1, 5):
        repos.cuentas.guardar(cuenta(f"RAD-{indice}", fecha_presentacion=date(2026, indice, 10)))
    repos.cuentas.guardar(cuenta("RAD-9", CONTRATO_B))

    pagina, total = repos.cuentas.buscar(FiltroCuentas(), pagina=2, tamano=2)
    por_contrato, total_b = repos.cuentas.buscar(FiltroCuentas(ids_contrato=(CONTRATO_B,)), 1, 10)
    por_fecha, _ = repos.cuentas.buscar(
        FiltroCuentas(desde=date(2026, 2, 10), hasta=date(2026, 3, 10)), 1, 10
    )
    vacio, cero = repos.cuentas.buscar(FiltroCuentas(ids_contrato=()), 1, 10)

    assert (total, [c.numero_radicado for c in pagina]) == (5, ["RAD-3", "RAD-4"])
    assert (total_b, [c.numero_radicado for c in por_contrato]) == (1, ["RAD-9"])
    assert [c.numero_radicado for c in por_fecha] == ["RAD-2", "RAD-3"]
    assert (vacio, cero) == ([], 0)


def test_suma_comprometida_y_resumenes(repos: Repositorios) -> None:
    repos.cuentas.guardar(cuenta("RAD-1", valor_cobro=ValorMonetario(Decimal("100.25"))))
    repos.cuentas.guardar(cuenta("RAD-2", valor_cobro=ValorMonetario(Decimal("50.00"))))
    anulada = cuenta("RAD-3", valor_cobro=ValorMonetario(Decimal("999.00")))
    anulada.cambiar_estado(EstadoCuenta.ANULADA, USUARIO)
    repos.cuentas.guardar(anulada)
    repos.cuentas.guardar(cuenta("RAD-4", CONTRATO_B))

    assert repos.cuentas.suma_comprometida(CONTRATO_A) == Decimal("150.25")
    assert repos.cuentas.suma_comprometida(CONTRATO_A, "RAD-1") == Decimal("50.00")
    assert repos.cuentas.suma_comprometida(str(ObjectId())) == Decimal(0)
    assert repos.cuentas.resumen_por_estado() == [
        ResumenGrupo("ANULADA", 1, Decimal("999.00")),
        ResumenGrupo("RECIBIDA", 3, Decimal("250.25")),
    ]
    assert sorted(repos.cuentas.resumen_por_contrato(), key=lambda g: g.clave) == sorted(
        [
            ResumenGrupo(CONTRATO_A, 3, Decimal("1149.25")),
            ResumenGrupo(CONTRATO_B, 1, Decimal("100.00")),
        ],
        key=lambda g: g.clave,
    )


def test_contratos_guardar_obtener_y_listar(repos: Repositorios) -> None:
    contratista = str(ObjectId())
    primero = contrato("CONT-1", contratista)
    repos.contratos.guardar(primero)
    repos.contratos.guardar(contrato("CONT-2"))
    assert primero.id is not None
    primero.cambiar_estado(EstadoContrato.SUSPENDIDO)
    repos.contratos.guardar(primero)

    assert repos.contratos.obtener_por_id(primero.id) == primero
    assert repos.contratos.obtener_por_id("no-es-id") is None
    assert [c.numero_contrato for c in repos.contratos.listar()] == ["CONT-1", "CONT-2"]
    assert [c.numero_contrato for c in repos.contratos.listar(contratista)] == ["CONT-1"]
    assert [
        c.numero_contrato for c in repos.contratos.listar(estado=EstadoContrato.SUSPENDIDO)
    ] == ["CONT-1"]
    with pytest.raises(RegistroDuplicadoError):
        repos.contratos.guardar(contrato("CONT-1"))


def test_contratistas_guardar_buscar_y_duplicado(repos: Repositorios) -> None:
    empresa = PersonaJuridica(nombre_completo="Constructora Sintética", nit_cedula="900000001")
    persona = PersonaNatural(nombre_completo="Ana Prueba", nit_cedula="52000001", activo=False)
    repos.contratistas.guardar(empresa)
    repos.contratistas.guardar(persona)
    assert empresa.id is not None

    assert repos.contratistas.obtener_por_id(empresa.id) == empresa
    assert [c.nombre_completo for c in repos.contratistas.buscar("SINTÉTICA")] == [
        "Constructora Sintética"
    ]
    assert [c.nit_cedula for c in repos.contratistas.buscar("5200")] == ["52000001"]
    assert [c.nombre_completo for c in repos.contratistas.buscar(solo_activos=True)] == [
        "Constructora Sintética"
    ]
    assert len(repos.contratistas.buscar()) == 2
    with pytest.raises(RegistroDuplicadoError):
        repos.contratistas.guardar(PersonaNatural(nombre_completo="Otra", nit_cedula="52000001"))


def test_roles_por_nombre_y_listado(repos: Repositorios) -> None:
    consulta = repos.roles.obtener_por_nombre("Consulta")

    assert consulta is not None
    assert consulta.tiene_permiso("cuentas.consultar")
    assert repos.roles.obtener_por_nombre("Inventado") is None
    assert [rol.nombre for rol in repos.roles.listar()] == sorted(
        rol.nombre for rol in roles_sinteticos()
    )


def test_archivos_guardar_leer_y_eliminar(repos: Repositorios) -> None:
    contenido = pdf_sintetico("Archivo de prueba") + b"0" * (600 * 1024)

    id_archivo = repos.archivos.guardar("prueba.pdf", contenido, "application/pdf")
    bloques = list(repos.archivos.leer_bloques(id_archivo))
    repos.archivos.eliminar(id_archivo)

    assert len(bloques) > 1
    assert b"".join(bloques) == contenido
    with pytest.raises(NoEncontradoError):
        repos.archivos.leer_bloques(id_archivo)
    repos.archivos.eliminar(id_archivo)


def test_auditoria_registra_y_filtra(repos: Repositorios) -> None:
    for minutos, tipo, usuario in [(0, "CuentaRadicada", "u1"), (5, "CuentaAnulada", "u2")]:
        repos.auditoria.registrar(
            RegistroEvento(
                id_evento=str(ObjectId()),
                tipo=tipo,
                ocurrido_en=MOMENTO + timedelta(minutes=minutos),
                id_usuario=usuario,
                descripcion=f"{tipo} sintético",
                datos={"numero_radicado": "RAD-1"},
            )
        )

    todos = repos.auditoria.buscar(FiltroAuditoria())
    por_usuario = repos.auditoria.buscar(FiltroAuditoria(id_usuario="u1"))
    desde = repos.auditoria.buscar(FiltroAuditoria(desde=MOMENTO + timedelta(minutes=1)))
    limitado = repos.auditoria.buscar(FiltroAuditoria(limite=1))

    assert [r.tipo for r in todos] == ["CuentaAnulada", "CuentaRadicada"]
    assert [r.tipo for r in por_usuario] == ["CuentaRadicada"]
    assert [r.tipo for r in desde] == ["CuentaAnulada"]
    assert len(limitado) == 1
    assert todos[0].datos == {"numero_radicado": "RAD-1"}
    assert todos[0].ocurrido_en == MOMENTO + timedelta(minutes=5)


def test_usuarios_listar(repos: Repositorios) -> None:
    for usuario in usuarios_sinteticos(roles_sinteticos()):
        repos.usuarios.guardar(usuario)

    correos = [usuario.correo for usuario in repos.usuarios.listar()]

    assert correos == sorted(correos)
    assert "administrador@example.com" in correos
