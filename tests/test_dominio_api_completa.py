from datetime import date
from decimal import Decimal

import pytest

from gestion_documental.datos_sinteticos import pdf_sintetico
from gestion_documental.domain.archivos import TAMANO_MAXIMO_BYTES, validar_archivo
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.documentos import DocumentoURL
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta, TipoDocumento
from gestion_documental.domain.errores import (
    ArchivoDemasiadoGrandeError,
    ArchivoInvalidoError,
    ErrorDominio,
    NoEncontradoError,
    TransicionInvalidaError,
)
from gestion_documental.domain.valores import ValorMonetario
from tests.fabricas import contrato_en_memoria

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


@pytest.mark.parametrize(
    ("contenido", "esperado"),
    [(pdf_sintetico("x"), "application/pdf"), (PNG, "image/png"), (JPG, "image/jpeg")],
)
def test_tipo_se_detecta_por_contenido(contenido: bytes, esperado: str) -> None:
    assert validar_archivo(contenido) == esperado


@pytest.mark.parametrize("contenido", [b"MZ ejecutable", b"<html>", b"PK\x03\x04 zip"])
def test_rechaza_tipos_no_permitidos(contenido: bytes) -> None:
    with pytest.raises(ArchivoInvalidoError, match="PDF, JPG o PNG"):
        validar_archivo(contenido)


def test_rechaza_vacio_y_mayor_a_10_mb() -> None:
    with pytest.raises(ArchivoInvalidoError, match="vacío"):
        validar_archivo(b"")
    with pytest.raises(ArchivoDemasiadoGrandeError):
        validar_archivo(b"%PDF-" + b"0" * TAMANO_MAXIMO_BYTES)


def test_contrato_solo_admite_radicacion_activo_y_vigente() -> None:
    contrato = contrato_en_memoria()

    contrato.verificar_radicacion(date(2026, 6, 1))
    with pytest.raises(ErrorDominio, match="fuera de la vigencia"):
        contrato.verificar_radicacion(date(2027, 1, 1))
    contrato.cambiar_estado(EstadoContrato.SUSPENDIDO)
    with pytest.raises(ErrorDominio, match="SUSPENDIDO"):
        contrato.verificar_radicacion(date(2026, 6, 1))


@pytest.mark.parametrize(
    ("camino", "destino", "valido"),
    [
        ([], EstadoContrato.SUSPENDIDO, True),
        ([EstadoContrato.SUSPENDIDO], EstadoContrato.ACTIVO, True),
        ([EstadoContrato.TERMINADO], EstadoContrato.LIQUIDADO, True),
        ([], EstadoContrato.LIQUIDADO, False),
        ([EstadoContrato.CANCELADO], EstadoContrato.ACTIVO, False),
    ],
)
def test_transiciones_de_contrato(
    camino: list[EstadoContrato], destino: EstadoContrato, valido: bool
) -> None:
    contrato = contrato_en_memoria()
    for estado in camino:
        contrato.cambiar_estado(estado)

    if valido:
        assert contrato.cambiar_estado(destino) == (camino[-1] if camino else EstadoContrato.ACTIVO)
    else:
        with pytest.raises(TransicionInvalidaError):
            contrato.cambiar_estado(destino)


def cuenta() -> CuentaCobro:
    nueva = CuentaCobro(
        numero_radicado="RAD-1",
        numero_cuenta="C-1",
        id_contrato="c",
        valor_cobro=ValorMonetario(Decimal("10.00")),
        concepto_pago="Concepto",
        fecha_presentacion=date(2026, 1, 1),
        id_usuario="u",
    )
    nueva.agregar_documento(
        DocumentoURL(
            nombre_original="rut.pdf",
            ruta_archivo="https://example.com/rut.pdf",
            tipo=TipoDocumento.RUT,
            id_usuario="u",
        )
    )
    return nueva


def test_editar_devuelve_solo_los_campos_que_cambian() -> None:
    editable = cuenta()

    campos = editable.editar(concepto_pago="Nuevo concepto", numero_cuenta="C-1")

    assert campos == ["concepto_pago"]
    assert editable.concepto_pago == "Nuevo concepto"


@pytest.mark.parametrize("estado", [EstadoCuenta.ANULADA])
def test_no_se_edita_ni_se_elimina_documento_fuera_de_recibida_o_revision(
    estado: EstadoCuenta,
) -> None:
    cerrada = cuenta()
    documento = cerrada.documentos[0]
    cerrada.cambiar_estado(estado, "u")

    with pytest.raises(ErrorDominio, match="solo se modifica"):
        cerrada.editar(concepto_pago="otro")
    with pytest.raises(ErrorDominio, match="solo se modifica"):
        cerrada.eliminar_documento(documento.id_documento)


def test_eliminar_documento() -> None:
    editable = cuenta()
    documento = editable.documentos[0]

    assert editable.eliminar_documento(documento.id_documento) == documento
    assert editable.documentos == ()
    with pytest.raises(NoEncontradoError):
        editable.documento(documento.id_documento)
