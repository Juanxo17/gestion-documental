from collections.abc import Callable
from decimal import Decimal

import pytest
from pydantic import ValidationError

from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento
from gestion_documental.events.comandos import AdjuntarDocumento, CambiarEstadoCuenta, RadicarCuenta
from gestion_documental.events.eventos import CuentaRadicada, EventoDominio
from tests.fabricas import cuenta_radicada, documento_adjuntado, estado_cambiado, radicar

EVENTOS: list[Callable[[], EventoDominio]] = [cuenta_radicada, estado_cambiado, documento_adjuntado]


@pytest.mark.parametrize("crear", EVENTOS, ids=lambda crear: crear.__name__)
def test_evento_es_inmutable(crear: Callable[[], EventoDominio]) -> None:
    evento = crear()

    with pytest.raises(ValidationError, match="frozen"):
        evento.id_usuario = "otro"  # type: ignore[misc]


def test_comando_es_inmutable() -> None:
    comando = radicar()

    with pytest.raises(ValidationError, match="frozen"):
        comando.valor_cobro = Decimal("1.00")  # type: ignore[misc]


def test_evento_base_es_abstracto() -> None:
    with pytest.raises(TypeError):
        EventoDominio(id_usuario="u1")  # type: ignore[abstract]


def test_cada_evento_tiene_id_y_fecha_propios() -> None:
    primero, segundo = cuenta_radicada(), cuenta_radicada()

    assert primero.id_evento != segundo.id_evento
    assert primero.ocurrido_en.tzinfo is not None


def test_str_es_polimorfico() -> None:
    textos = [str(crear()) for crear in EVENTOS]

    assert textos[0].startswith("[CuentaRadicada]")
    assert "de EN_REVISION a APROBADA" in textos[1]
    assert "adjuntó rut_sintetico.pdf" in textos[2]


def test_evento_rechaza_campos_desconocidos() -> None:
    with pytest.raises(ValidationError, match="extra"):
        CuentaRadicada(
            id_usuario="u1",
            numero_radicado="RAD-1",
            id_contrato="c1",
            valor_cobro=Decimal("1.00"),
            campo_inventado="x",  # type: ignore[call-arg]
        )


@pytest.mark.parametrize("valor", [Decimal(0), Decimal("-5"), Decimal("1.001")])
def test_radicar_valida_el_valor(valor: Decimal) -> None:
    with pytest.raises(ValidationError, match="valor_cobro"):
        RadicarCuenta.model_validate({**radicar().model_dump(), "valor_cobro": valor})


def test_radicar_exige_usuario() -> None:
    with pytest.raises(ValidationError, match="id_usuario"):
        RadicarCuenta.model_validate({**radicar().model_dump(), "id_usuario": "   "})


def test_cambiar_estado_solo_acepta_estados_conocidos() -> None:
    with pytest.raises(ValidationError, match="nuevo_estado"):
        CambiarEstadoCuenta.model_validate(
            {"id_usuario": "u1", "numero_radicado": "RAD-1", "nuevo_estado": "PERDIDA"}
        )


def test_cambiar_estado_convierte_texto_en_enum() -> None:
    comando = CambiarEstadoCuenta.model_validate(
        {"id_usuario": "u1", "numero_radicado": "RAD-1", "nuevo_estado": "EN_REVISION"}
    )

    assert comando.nuevo_estado is EstadoCuenta.EN_REVISION


def test_adjuntar_documento_valida_tamano() -> None:
    with pytest.raises(ValidationError, match="tamano_bytes"):
        AdjuntarDocumento(
            id_usuario="u1",
            numero_radicado="RAD-1",
            nombre_original="a.pdf",
            ruta_archivo="/uploads/a.pdf",
            tipo=TipoDocumento.OTRO,
            origen=OrigenDocumento.LOCAL,
            tamano_bytes=0,
        )
