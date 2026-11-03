import hashlib
import inspect
from collections.abc import Callable
from dataclasses import FrozenInstanceError
from typing import Any

import pytest

from gestion_documental.domain.documentos import (
    Documento,
    DocumentoLocal,
    DocumentoPDF,
    DocumentoURL,
)
from gestion_documental.domain.enums import OrigenDocumento, TipoDocumento
from gestion_documental.domain.errores import ErrorDominio

CONTENIDO = b"contenido sintetico de prueba"
HASH = hashlib.sha256(CONTENIDO).hexdigest()
COMUNES: dict[str, Any] = {"tipo": TipoDocumento.CUENTA_COBRO, "id_usuario": "usuario-sintetico-1"}
CAMPOS_COMUNES = {"nombre_original", "ruta_archivo", "tipo", "id_usuario", "fecha_carga"}


def local(**cambios: Any) -> DocumentoLocal:
    datos: dict[str, Any] = {
        **COMUNES,
        "nombre_original": "anexo_sintetico.docx",
        "ruta_archivo": "/uploads/anexo_sintetico.docx",
        "tipo_mime": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "hash_sha256": HASH,
        "tamano_bytes": len(CONTENIDO),
        **cambios,
    }
    return DocumentoLocal(**datos)


def pdf(**cambios: Any) -> DocumentoPDF:
    datos: dict[str, Any] = {
        **COMUNES,
        "nombre_original": "cuenta_sintetica.pdf",
        "ruta_archivo": "/uploads/cuenta_sintetica.pdf",
        "tipo_mime": "application/pdf",
        "hash_sha256": HASH,
        "tamano_bytes": len(CONTENIDO),
        **cambios,
    }
    return DocumentoPDF(**datos)


def url(**cambios: Any) -> DocumentoURL:
    datos: dict[str, Any] = {
        **COMUNES,
        "nombre_original": "rut_sintetico.pdf",
        "ruta_archivo": "https://example.com/rut_sintetico.pdf",
        **cambios,
    }
    return DocumentoURL(**datos)


EJEMPLOS: dict[type[Documento], Callable[[], Documento]] = {
    DocumentoLocal: local,
    DocumentoPDF: pdf,
    DocumentoURL: url,
}


CLASES = sorted(EJEMPLOS, key=lambda clase: clase.__name__)
NOMBRES = [clase.__name__ for clase in CLASES]


def subclases_concretas(clase: type[Any]) -> set[type[Any]]:
    encontradas: set[type[Any]] = set()
    for subclase in clase.__subclasses__():
        if not inspect.isabstract(subclase):
            encontradas.add(subclase)
        encontradas |= subclases_concretas(subclase)
    return encontradas


def usar_como_documento(documento: Documento) -> dict[str, Any]:
    documento.validar()
    descripcion = documento.describir()
    datos = documento.a_dict()
    assert isinstance(descripcion, str)
    assert descripcion
    assert datos.keys() >= CAMPOS_COMUNES
    assert datos["origen"] == documento.origen.value
    assert datos["descripcion"] == descripcion
    return datos


def test_cada_subclase_concreta_tiene_ejemplo() -> None:
    assert subclases_concretas(Documento) == set(EJEMPLOS)


@pytest.mark.parametrize("clase", CLASES, ids=NOMBRES)
def test_lsp_cualquier_subclase_sirve_como_documento(clase: type[Documento]) -> None:
    documento = EJEMPLOS[clase]()

    assert isinstance(documento, Documento)
    usar_como_documento(documento)


@pytest.mark.parametrize("clase", CLASES, ids=NOMBRES)
def test_jerarquia_de_documento_no_supera_tres_niveles(clase: type[Documento]) -> None:
    niveles = [ancestro for ancestro in clase.__mro__ if issubclass(ancestro, Documento)]

    assert len(niveles) <= 3


def test_documento_abstracto_no_se_puede_instanciar() -> None:
    with pytest.raises(TypeError):
        Documento(**COMUNES, nombre_original="x", ruta_archivo="x")  # type: ignore[abstract]


def test_check_metadatos_falla_para_local_incompleto() -> None:
    with pytest.raises(ErrorDominio, match="exige tipo_mime, hash_sha256 y tamano_bytes"):
        local(tipo_mime=None, hash_sha256=None, tamano_bytes=None)


@pytest.mark.parametrize("faltante", ["tipo_mime", "hash_sha256", "tamano_bytes"])
def test_check_metadatos_falla_si_falta_uno(faltante: str) -> None:
    with pytest.raises(ErrorDominio):
        local(**{faltante: None})


def test_check_metadatos_no_aplica_a_url() -> None:
    documento = url()

    assert documento.origen is OrigenDocumento.URL
    assert "tipo_mime" not in documento.a_dict()


@pytest.mark.parametrize("hash_invalido", ["abc", "G" * 64, HASH.upper()])
def test_local_rechaza_hash_invalido(hash_invalido: str) -> None:
    with pytest.raises(ErrorDominio, match="hash_sha256"):
        local(hash_sha256=hash_invalido)


@pytest.mark.parametrize("tamano", [0, -1])
def test_local_rechaza_tamano_no_positivo(tamano: int) -> None:
    with pytest.raises(ErrorDominio, match="tamano_bytes"):
        local(tamano_bytes=tamano)


def test_verificar_hash() -> None:
    documento = local()

    assert documento.verificar_hash(CONTENIDO)
    assert not documento.verificar_hash(b"contenido alterado")


@pytest.mark.parametrize("ruta", ["/uploads/archivo.pdf", "ftp://example.com/a.pdf", "https://"])
def test_url_exige_http_o_https(ruta: str) -> None:
    with pytest.raises(ErrorDominio, match="http o https"):
        url(ruta_archivo=ruta)


def test_pdf_exige_mime_pdf() -> None:
    with pytest.raises(ErrorDominio, match="application/pdf"):
        pdf(tipo_mime="image/jpeg")


def test_pdf_hereda_reglas_de_local() -> None:
    with pytest.raises(ErrorDominio, match="exige tipo_mime"):
        pdf(hash_sha256=None)


def test_describir_se_resuelve_en_tiempo_de_ejecucion() -> None:
    documentos: list[Documento] = [local(), pdf(), url()]

    descripciones = [documento.describir() for documento in documentos]

    assert descripciones[0].startswith("Archivo local")
    assert descripciones[1].startswith("PDF")
    assert descripciones[2].startswith("Enlace externo")


def test_documento_es_inmutable() -> None:
    documento = url()

    with pytest.raises(FrozenInstanceError):
        documento.nombre_original = "otro.pdf"  # type: ignore[misc]
