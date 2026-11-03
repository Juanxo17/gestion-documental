from abc import ABC

import pytest

from gestion_documental.domain.contratistas import (
    Contratista,
    PersonaJuridica,
    PersonaNatural,
    digito_verificacion_nit,
)
from gestion_documental.domain.enums import TipoPersona
from gestion_documental.domain.errores import ErrorDominio
from gestion_documental.domain.mixins import AuditableMixin

NIT_VALIDO = "900000001-2"


def test_mro_del_mixin() -> None:
    assert PersonaJuridica.__mro__ == (
        PersonaJuridica,
        Contratista,
        AuditableMixin,
        ABC,
        object,
    )
    assert PersonaNatural.__mro__[1:] == PersonaJuridica.__mro__[1:]


def test_mixin_registra_quien_y_cuando() -> None:
    contratista = PersonaNatural(nombre_completo="Persona Sintética", nit_cedula="1000000001")

    contratista.registrar_creacion("admin-sintetico")
    contratista.registrar_modificacion("revisor-sintetico")

    assert contratista.creado_por == "admin-sintetico"
    assert contratista.modificado_por == "revisor-sintetico"
    assert contratista.creado_en is not None
    assert contratista.modificado_en is not None


def test_mixin_no_permite_modificar_antes_de_crear() -> None:
    contratista = PersonaNatural(nombre_completo="Persona Sintética", nit_cedula="1000000001")

    with pytest.raises(ErrorDominio):
        contratista.registrar_modificacion("revisor-sintetico")


def test_contratista_abstracto_no_se_puede_instanciar() -> None:
    with pytest.raises(TypeError):
        Contratista(nombre_completo="X", nit_cedula="1")  # type: ignore[abstract]


@pytest.mark.parametrize("cedula", ["123456", "1000000001"])
def test_cedula_valida(cedula: str) -> None:
    contratista = PersonaNatural(nombre_completo="Persona Sintética", nit_cedula=cedula)

    assert contratista.tipo_persona is TipoPersona.NATURAL


@pytest.mark.parametrize("cedula", ["12345", "12345678901", "0123456", "12A456", NIT_VALIDO])
def test_cedula_invalida(cedula: str) -> None:
    with pytest.raises(ErrorDominio, match="cédula"):
        PersonaNatural(nombre_completo="Persona Sintética", nit_cedula=cedula)


def test_digito_verificacion() -> None:
    assert digito_verificacion_nit("900000001") == 2
    assert digito_verificacion_nit("901234567") == 7


@pytest.mark.parametrize("nit", [NIT_VALIDO, "900000001", "901234567"])
def test_nit_valido_con_o_sin_digito(nit: str) -> None:
    contratista = PersonaJuridica(nombre_completo="Empresa Sintética S.A.S.", nit_cedula=nit)

    assert contratista.tipo_persona is TipoPersona.JURIDICA


@pytest.mark.parametrize(
    "nit", ["900000001-", "90000001-2", "1000000001", "90000000A", "900000001-23"]
)
def test_nit_con_formato_invalido(nit: str) -> None:
    with pytest.raises(ErrorDominio, match="formato"):
        PersonaJuridica(nombre_completo="Empresa Sintética S.A.S.", nit_cedula=nit)


def test_nit_con_digito_invalido() -> None:
    with pytest.raises(ErrorDominio, match="dígito de verificación"):
        PersonaJuridica(nombre_completo="Empresa Sintética S.A.S.", nit_cedula="900000001-3")


def test_nombre_obligatorio() -> None:
    with pytest.raises(ErrorDominio, match="nombre_completo"):
        PersonaNatural(nombre_completo="  ", nit_cedula="1000000001")
