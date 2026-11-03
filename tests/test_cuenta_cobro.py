from datetime import date
from decimal import Decimal

import pytest

from gestion_documental.domain.cuenta_cobro import CambioEstado, CuentaCobro
from gestion_documental.domain.documentos import DocumentoPDF, DocumentoURL
from gestion_documental.domain.enums import EstadoCuenta, TipoDocumento
from gestion_documental.domain.errores import ErrorDominio, TransicionInvalidaError
from gestion_documental.domain.valores import ValorMonetario

E = EstadoCuenta


def nueva_cuenta() -> CuentaCobro:
    return CuentaCobro(
        numero_radicado="RAD-SINT-0001",
        numero_cuenta="CUENTA-001",
        id_contrato="contrato-sintetico-1",
        valor_cobro=ValorMonetario(Decimal("1500000.00")),
        concepto_pago="Honorarios sintéticos del mes",
        fecha_presentacion=date(2026, 1, 31),
        id_usuario="radicador-sintetico",
    )


def documento_url() -> DocumentoURL:
    return DocumentoURL(
        nombre_original="rut_sintetico.pdf",
        ruta_archivo="https://example.com/rut_sintetico.pdf",
        tipo=TipoDocumento.RUT,
        id_usuario="radicador-sintetico",
    )


def documento_pdf() -> DocumentoPDF:
    return DocumentoPDF(
        nombre_original="cuenta_sintetica.pdf",
        ruta_archivo="/uploads/cuenta_sintetica.pdf",
        tipo=TipoDocumento.CUENTA_COBRO,
        id_usuario="radicador-sintetico",
        tipo_mime="application/pdf",
        hash_sha256="0" * 64,
        tamano_bytes=1024,
    )


def llevar_a(cuenta: CuentaCobro, camino: list[EstadoCuenta]) -> None:
    for estado in camino:
        cuenta.cambiar_estado(estado, id_usuario="revisor-sintetico")


def test_cuenta_nueva_empieza_recibida_con_historial() -> None:
    cuenta = nueva_cuenta()

    assert cuenta.estado is E.RECIBIDA
    assert len(cuenta.historial) == 1
    assert cuenta.historial[0].estado_anterior is None


@pytest.mark.parametrize(
    "camino",
    [
        [E.EN_REVISION, E.APROBADA, E.PAGADA],
        [E.EN_REVISION, E.RECHAZADA],
        [E.ANULADA],
        [E.EN_REVISION, E.ANULADA],
        [E.EN_REVISION, E.APROBADA, E.ANULADA],
    ],
    ids=lambda camino: "->".join(camino),
)
def test_transiciones_validas(camino: list[EstadoCuenta]) -> None:
    cuenta = nueva_cuenta()

    llevar_a(cuenta, camino)

    assert cuenta.estado is camino[-1]
    assert [cambio.estado_nuevo for cambio in cuenta.historial] == [E.RECIBIDA, *camino]
    assert cuenta.historial[-1].estado_anterior is ([E.RECIBIDA, *camino][-2])


@pytest.mark.parametrize(
    ("camino_previo", "destino"),
    [
        ([], E.APROBADA),
        ([], E.PAGADA),
        ([], E.RECIBIDA),
        ([E.EN_REVISION], E.PAGADA),
        ([E.EN_REVISION, E.RECHAZADA], E.ANULADA),
        ([E.EN_REVISION, E.APROBADA, E.PAGADA], E.ANULADA),
        ([E.ANULADA], E.EN_REVISION),
    ],
)
def test_transiciones_invalidas(camino_previo: list[EstadoCuenta], destino: EstadoCuenta) -> None:
    cuenta = nueva_cuenta()
    llevar_a(cuenta, camino_previo)
    historial_antes = cuenta.historial

    with pytest.raises(TransicionInvalidaError):
        cuenta.cambiar_estado(destino, id_usuario="revisor-sintetico")

    assert cuenta.historial == historial_antes


def test_cambio_registra_usuario_y_observacion() -> None:
    cuenta = nueva_cuenta()

    cambio = cuenta.cambiar_estado(E.EN_REVISION, "revisor-sintetico", "Revisión de soportes")

    assert cambio.id_usuario == "revisor-sintetico"
    assert cambio.observacion == "Revisión de soportes"


def test_composicion_acepta_cualquier_documento() -> None:
    cuenta = nueva_cuenta()

    cuenta.agregar_documento(documento_pdf())
    cuenta.agregar_documento(documento_url())

    assert [type(documento) for documento in cuenta.documentos] == [DocumentoPDF, DocumentoURL]


def test_no_se_agregan_documentos_a_cuenta_final() -> None:
    cuenta = nueva_cuenta()
    llevar_a(cuenta, [E.ANULADA])

    with pytest.raises(ErrorDominio, match="ANULADA"):
        cuenta.agregar_documento(documento_url())


def test_documentos_e_historial_no_se_modifican_desde_fuera() -> None:
    cuenta = nueva_cuenta()

    assert isinstance(cuenta.documentos, tuple)
    assert isinstance(cuenta.historial, tuple)


def test_cuenta_cobro_no_hereda_del_dominio() -> None:
    assert CuentaCobro.__mro__ == (CuentaCobro, object)


def test_reconstruir_desde_historial_guardado() -> None:
    historial = [
        CambioEstado(estado_anterior=None, estado_nuevo=E.RECIBIDA, id_usuario="u1"),
        CambioEstado(estado_anterior=E.RECIBIDA, estado_nuevo=E.APROBADA, id_usuario="u2"),
    ]
    cuenta = CuentaCobro(
        numero_radicado="RAD-SINT-0002",
        numero_cuenta="CUENTA-001",
        id_contrato="contrato-sintetico-2",
        valor_cobro=ValorMonetario(Decimal("10.00")),
        concepto_pago="Concepto sintético",
        fecha_presentacion=date(2026, 2, 1),
        id_usuario="u1",
        historial=historial,
    )

    assert cuenta.estado is E.APROBADA
