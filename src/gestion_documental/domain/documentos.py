import hashlib
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, fields
from datetime import UTC, datetime
from typing import Any, ClassVar
from urllib.parse import urlparse

from gestion_documental.domain.enums import OrigenDocumento, TipoDocumento
from gestion_documental.domain.errores import ErrorDominio

PATRON_SHA256 = re.compile(r"[0-9a-f]{64}")
ESQUEMAS_URL = frozenset({"http", "https"})
MIME_PDF = "application/pdf"


@dataclass(frozen=True, kw_only=True)
class Documento(ABC):
    origen: ClassVar[OrigenDocumento]

    nombre_original: str
    ruta_archivo: str
    tipo: TipoDocumento
    id_usuario: str
    fecha_carga: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        self.validar()

    @abstractmethod
    def validar(self) -> None:
        if not self.nombre_original.strip():
            raise ErrorDominio("El documento necesita nombre_original")
        if not self.ruta_archivo.strip():
            raise ErrorDominio("El documento necesita ruta_archivo")
        if not self.id_usuario.strip():
            raise ErrorDominio("El documento necesita id_usuario")

    @abstractmethod
    def describir(self) -> str: ...

    def a_dict(self) -> dict[str, Any]:
        self.validar()
        datos: dict[str, Any] = {campo.name: getattr(self, campo.name) for campo in fields(self)}
        datos["tipo"] = self.tipo.value
        datos["origen"] = self.origen.value
        datos["descripcion"] = self.describir()
        return datos


@dataclass(frozen=True, kw_only=True)
class DocumentoLocal(Documento):
    origen: ClassVar[OrigenDocumento] = OrigenDocumento.LOCAL

    tipo_mime: str | None = None
    hash_sha256: str | None = None
    tamano_bytes: int | None = None

    def validar(self) -> None:
        super().validar()
        if self.tipo_mime is None or self.hash_sha256 is None or self.tamano_bytes is None:
            raise ErrorDominio("Un documento LOCAL exige tipo_mime, hash_sha256 y tamano_bytes")
        if not PATRON_SHA256.fullmatch(self.hash_sha256):
            raise ErrorDominio("hash_sha256 debe tener 64 caracteres hexadecimales en minúscula")
        if self.tamano_bytes <= 0:
            raise ErrorDominio("tamano_bytes debe ser mayor que cero")

    def describir(self) -> str:
        return f"Archivo local {self.nombre_original} ({self.tipo_mime}, {self.tamano_bytes} bytes)"

    def verificar_hash(self, contenido: bytes) -> bool:
        return hashlib.sha256(contenido).hexdigest() == self.hash_sha256


@dataclass(frozen=True, kw_only=True)
class DocumentoURL(Documento):
    origen: ClassVar[OrigenDocumento] = OrigenDocumento.URL

    def validar(self) -> None:
        super().validar()
        url = urlparse(self.ruta_archivo)
        if url.scheme not in ESQUEMAS_URL or not url.netloc:
            raise ErrorDominio("Un documento URL exige una ruta http o https")

    def describir(self) -> str:
        return f"Enlace externo {self.nombre_original} en {urlparse(self.ruta_archivo).netloc}"


@dataclass(frozen=True, kw_only=True)
class DocumentoPDF(DocumentoLocal):
    def validar(self) -> None:
        super().validar()
        if self.tipo_mime != MIME_PDF:
            raise ErrorDominio(f"Un DocumentoPDF exige tipo_mime {MIME_PDF}")

    def describir(self) -> str:
        return f"PDF {self.nombre_original} ({self.tamano_bytes} bytes)"
