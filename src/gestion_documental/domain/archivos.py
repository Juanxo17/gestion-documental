import hashlib

from gestion_documental.domain.errores import ArchivoDemasiadoGrandeError, ArchivoInvalidoError

TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024
FIRMAS: dict[bytes, str] = {
    b"%PDF-": "application/pdf",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"\xff\xd8\xff": "image/jpeg",
}


def detectar_tipo_mime(contenido: bytes) -> str:
    for firma, tipo_mime in FIRMAS.items():
        if contenido.startswith(firma):
            return tipo_mime
    raise ArchivoInvalidoError("Solo se aceptan archivos PDF, JPG o PNG (según su contenido)")


def validar_archivo(contenido: bytes) -> str:
    if not contenido:
        raise ArchivoInvalidoError("El archivo está vacío")
    if len(contenido) > TAMANO_MAXIMO_BYTES:
        raise ArchivoDemasiadoGrandeError("El archivo supera el máximo de 10 MB")
    return detectar_tipo_mime(contenido)


def sha256(contenido: bytes) -> str:
    return hashlib.sha256(contenido).hexdigest()
