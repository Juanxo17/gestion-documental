import hashlib
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

import pytest
from bson import ObjectId

from gestion_documental.domain.contratistas import Contratista, PersonaJuridica, PersonaNatural
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CambioEstado, CuentaCobro
from gestion_documental.domain.documentos import DocumentoLocal, DocumentoPDF, DocumentoURL
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta, TipoDocumento
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.repositories.base import (
    RegistroDuplicadoError,
    RepositorioContratistas,
    RepositorioContratos,
    RepositorioCuentas,
)
from gestion_documental.repositories.mapeo import (
    COLECCION_CONTRATISTAS,
    COLECCION_CONTRATOS,
    contratista_a_dict,
    contrato_a_dict,
)
from gestion_documental.repositories.memoria import (
    RepositorioContratistasEnMemoria,
    RepositorioContratosEnMemoria,
    RepositorioCuentasEnMemoria,
)
from gestion_documental.repositories.mongo import (
    RepositorioContratistasMongo,
    RepositorioContratosMongo,
    RepositorioCuentasMongo,
)

RADICADOR = str(ObjectId())
REVISOR = str(ObjectId())
CONTRATO_A = str(ObjectId())
CONTRATO_B = str(ObjectId())
CONTRATISTA = str(ObjectId())
SUPERVISOR = str(ObjectId())
CONTENIDO = b"contenido sintetico"
MOMENTO = datetime(2026, 1, 31, 9, 15, 30, 123000, tzinfo=UTC)


@dataclass
class Repositorios:
    cuentas: RepositorioCuentas
    contratos: RepositorioContratos
    contratistas: RepositorioContratistas


def contrato_sintetico() -> Contrato:
    return Contrato(
        id=CONTRATO_A,
        numero_contrato="CONT-SINT-001",
        id_contratista=CONTRATISTA,
        objeto_contrato="Objeto sintético de prueba",
        valor_total=ValorMonetario(Decimal("1000000.00")),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        estado=EstadoContrato.ACTIVO,
        id_supervisor=SUPERVISOR,
    )


def contratistas_sinteticos() -> list[Contratista]:
    juridica = PersonaJuridica(
        id=str(ObjectId()),
        nombre_completo="Empresa Sintética S.A.S.",
        nit_cedula="900000001-2",
        correo="contacto@example.com",
    )
    juridica.registrar_creacion(RADICADOR)
    natural = PersonaNatural(
        id=str(ObjectId()), nombre_completo="Persona Sintética", nit_cedula="1000000001"
    )
    return [juridica, natural]


def cuenta(radicado: str = "RAD-SINT-0001", **cambios: Any) -> CuentaCobro:
    datos: dict[str, Any] = {
        "numero_radicado": radicado,
        "numero_cuenta": "CUENTA-001",
        "id_contrato": CONTRATO_A,
        "valor_cobro": ValorMonetario(Decimal("1500000.50")),
        "concepto_pago": "Honorarios sintéticos",
        "fecha_presentacion": date(2026, 1, 31),
        "id_usuario": RADICADOR,
        **cambios,
    }
    return CuentaCobro(**datos)


def cuenta_completa() -> CuentaCobro:
    completa = cuenta(
        observaciones="Con soportes completos",
        historial=[
            CambioEstado(
                estado_anterior=None,
                estado_nuevo=EstadoCuenta.RECIBIDA,
                id_usuario=RADICADOR,
                observacion="Cuenta radicada",
                fecha_cambio=MOMENTO,
            )
        ],
    )
    comunes: dict[str, Any] = {"id_usuario": RADICADOR, "fecha_carga": MOMENTO}
    completa.agregar_documento(
        DocumentoPDF(
            **comunes,
            nombre_original="cuenta_sintetica.pdf",
            ruta_archivo="/uploads/cuenta_sintetica.pdf",
            tipo=TipoDocumento.CUENTA_COBRO,
            tipo_mime="application/pdf",
            hash_sha256=hashlib.sha256(CONTENIDO).hexdigest(),
            tamano_bytes=len(CONTENIDO),
        )
    )
    completa.agregar_documento(
        DocumentoLocal(
            **comunes,
            nombre_original="certificado_sintetico.docx",
            ruta_archivo="/uploads/certificado_sintetico.docx",
            tipo=TipoDocumento.CERTIFICADO,
            tipo_mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            hash_sha256=hashlib.sha256(b"otro").hexdigest(),
            tamano_bytes=3,
        )
    )
    completa.agregar_documento(
        DocumentoURL(
            **comunes,
            nombre_original="rut_sintetico.pdf",
            ruta_archivo="https://example.com/rut_sintetico.pdf",
            tipo=TipoDocumento.RUT,
        )
    )
    completa.cambiar_estado(EstadoCuenta.EN_REVISION, REVISOR, "Revisión de soportes")
    return completa


def instantanea(cuenta: CuentaCobro) -> tuple[Any, ...]:
    return (
        cuenta.numero_radicado,
        cuenta.numero_cuenta,
        cuenta.id_contrato,
        cuenta.valor_cobro,
        cuenta.concepto_pago,
        cuenta.fecha_presentacion,
        cuenta.id_usuario,
        cuenta.observaciones,
        cuenta.estado,
        cuenta.documentos,
        cuenta.historial,
    )


@pytest.fixture(params=["memoria", pytest.param("mongo", marks=pytest.mark.integracion)])
def repos(request: pytest.FixtureRequest) -> Repositorios:
    contrato = contrato_sintetico()
    contratistas = contratistas_sinteticos()
    if request.param == "memoria":
        return Repositorios(
            cuentas=RepositorioCuentasEnMemoria(),
            contratos=RepositorioContratosEnMemoria([contrato]),
            contratistas=RepositorioContratistasEnMemoria(contratistas),
        )
    db = request.getfixturevalue("db_pruebas")
    db[COLECCION_CONTRATOS].insert_one(contrato_a_dict(contrato))
    db[COLECCION_CONTRATISTAS].insert_many(contratista_a_dict(c) for c in contratistas)
    return Repositorios(
        cuentas=RepositorioCuentasMongo(db),
        contratos=RepositorioContratosMongo(db),
        contratistas=RepositorioContratistasMongo(db),
    )


def test_ida_y_vuelta_con_documentos_e_historial(repos: Repositorios) -> None:
    original = cuenta_completa()

    repos.cuentas.guardar(original)
    recuperada = repos.cuentas.obtener_por_radicado(original.numero_radicado)

    assert recuperada is not None
    assert instantanea(recuperada) == instantanea(original)
    assert [type(d) for d in recuperada.documentos] == [DocumentoPDF, DocumentoLocal, DocumentoURL]


def test_obtener_radicado_inexistente(repos: Repositorios) -> None:
    assert repos.cuentas.obtener_por_radicado("RAD-NO-EXISTE") is None


def test_guardar_dos_veces_actualiza_la_misma_cuenta(repos: Repositorios) -> None:
    nueva = cuenta()
    repos.cuentas.guardar(nueva)
    nueva.cambiar_estado(EstadoCuenta.EN_REVISION, REVISOR)

    repos.cuentas.guardar(nueva)

    recuperada = repos.cuentas.obtener_por_radicado(nueva.numero_radicado)
    assert recuperada is not None
    assert recuperada.estado is EstadoCuenta.EN_REVISION
    assert len(recuperada.historial) == 2
    assert repos.cuentas.listar_por_estado(EstadoCuenta.RECIBIDA) == []


def test_cambios_sin_guardar_no_se_persisten(repos: Repositorios) -> None:
    nueva = cuenta()
    repos.cuentas.guardar(nueva)

    nueva.cambiar_estado(EstadoCuenta.ANULADA, REVISOR)

    recuperada = repos.cuentas.obtener_por_radicado(nueva.numero_radicado)
    assert recuperada is not None
    assert recuperada.estado is EstadoCuenta.RECIBIDA


def test_listar_por_estado(repos: Repositorios) -> None:
    for radicado, numero in [("RAD-3", "C-3"), ("RAD-1", "C-1"), ("RAD-2", "C-2")]:
        repos.cuentas.guardar(cuenta(radicado, numero_cuenta=numero))
    revisada = cuenta("RAD-4", numero_cuenta="C-4")
    revisada.cambiar_estado(EstadoCuenta.EN_REVISION, REVISOR)
    repos.cuentas.guardar(revisada)

    recibidas = repos.cuentas.listar_por_estado(EstadoCuenta.RECIBIDA)
    en_revision = repos.cuentas.listar_por_estado(EstadoCuenta.EN_REVISION)

    assert [c.numero_radicado for c in recibidas] == ["RAD-1", "RAD-2", "RAD-3"]
    assert [c.numero_radicado for c in en_revision] == ["RAD-4"]
    assert repos.cuentas.listar_por_estado(EstadoCuenta.PAGADA) == []


def test_existe_numero_cuenta(repos: Repositorios) -> None:
    repos.cuentas.guardar(cuenta())

    assert repos.cuentas.existe_numero_cuenta(CONTRATO_A, "CUENTA-001")
    assert not repos.cuentas.existe_numero_cuenta(CONTRATO_A, "CUENTA-002")
    assert not repos.cuentas.existe_numero_cuenta(CONTRATO_B, "CUENTA-001")


def test_numero_cuenta_unico_por_contrato(repos: Repositorios) -> None:
    repos.cuentas.guardar(cuenta("RAD-1"))
    repos.cuentas.guardar(cuenta("RAD-2", id_contrato=CONTRATO_B))

    with pytest.raises(RegistroDuplicadoError):
        repos.cuentas.guardar(cuenta("RAD-3"))

    assert repos.cuentas.obtener_por_radicado("RAD-3") is None


def test_obtener_contrato_por_numero(repos: Repositorios) -> None:
    assert repos.contratos.obtener_por_numero("CONT-SINT-001") == contrato_sintetico()
    assert repos.contratos.obtener_por_numero("CONT-NO-EXISTE") is None


def test_obtener_contratista_reconstruye_la_subclase(repos: Repositorios) -> None:
    _, natural = contratistas_sinteticos()

    encontrada = repos.contratistas.obtener_por_identificacion("900000001-2")
    encontrado = repos.contratistas.obtener_por_identificacion("1000000001")

    assert isinstance(encontrada, PersonaJuridica)
    assert isinstance(encontrado, PersonaNatural)
    assert encontrada.creado_por == RADICADOR
    assert encontrado.nombre_completo == natural.nombre_completo
    assert repos.contratistas.obtener_por_identificacion("123456789") is None
