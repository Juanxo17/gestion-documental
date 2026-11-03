from dataclasses import FrozenInstanceError
from datetime import date
from decimal import Decimal
from typing import Any

import pytest

from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.errores import ErrorDominio
from gestion_documental.domain.valores import ValorMonetario


def test_valor_monetario_valido() -> None:
    assert ValorMonetario(Decimal("1500000.50")).monto == Decimal("1500000.50")


@pytest.mark.parametrize("monto", [Decimal(0), Decimal("-1"), Decimal("NaN"), Decimal("Infinity")])
def test_valor_monetario_debe_ser_positivo(monto: Decimal) -> None:
    with pytest.raises(ErrorDominio, match="mayor que cero"):
        ValorMonetario(monto)


def test_valor_monetario_maximo_dos_decimales() -> None:
    with pytest.raises(ErrorDominio, match="dos decimales"):
        ValorMonetario(Decimal("10.001"))


@pytest.mark.parametrize("monto", [10.5, 10])
def test_valor_monetario_rechaza_float_e_int(monto: Any) -> None:
    with pytest.raises(ErrorDominio, match="Decimal"):
        ValorMonetario(monto)


def test_valor_monetario_es_inmutable() -> None:
    valor = ValorMonetario(Decimal("1.00"))

    with pytest.raises(FrozenInstanceError):
        valor.monto = Decimal("2.00")  # type: ignore[misc]


def test_valores_iguales_son_iguales() -> None:
    assert ValorMonetario(Decimal("5.00")) == ValorMonetario(Decimal("5.00"))


def contrato(fecha_inicio: date, fecha_fin: date) -> Contrato:
    return Contrato(
        numero_contrato="CONT-SINT-001",
        id_contratista="contratista-sintetico",
        objeto_contrato="Objeto sintético de prueba",
        valor_total=ValorMonetario(Decimal("1000000.00")),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        id_supervisor="supervisor-sintetico",
    )


def test_contrato_acepta_mismo_dia() -> None:
    assert contrato(date(2026, 1, 1), date(2026, 1, 1)).fecha_fin == date(2026, 1, 1)


def test_contrato_rechaza_fin_antes_de_inicio() -> None:
    with pytest.raises(ErrorDominio, match="fecha_fin"):
        contrato(date(2026, 2, 1), date(2026, 1, 1))
