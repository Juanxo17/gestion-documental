import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import ClassVar

from gestion_documental.domain.enums import TipoPersona
from gestion_documental.domain.errores import ErrorDominio
from gestion_documental.domain.mixins import AuditableMixin

PATRON_CEDULA = re.compile(r"[1-9]\d{5,9}")
PATRON_NIT = re.compile(r"(\d{9})(?:-(\d))?")
PESOS_NIT = (3, 7, 13, 17, 19, 23, 29, 37, 41, 43, 47, 53, 59, 67, 71)


def digito_verificacion_nit(numero: str) -> int:
    suma = sum(
        int(digito) * peso for digito, peso in zip(reversed(numero), PESOS_NIT, strict=False)
    )
    residuo = suma % 11
    return residuo if residuo < 2 else 11 - residuo


@dataclass(kw_only=True)
class Contratista(AuditableMixin, ABC):
    tipo_persona: ClassVar[TipoPersona]

    nombre_completo: str
    nit_cedula: str
    telefono: str | None = None
    correo: str | None = None
    direccion: str | None = None
    activo: bool = True
    id: str | None = None

    def __post_init__(self) -> None:
        self.validar()

    def validar(self) -> None:
        if not self.nombre_completo.strip():
            raise ErrorDominio("El contratista necesita nombre_completo")
        self.validar_identificacion()

    def desactivar(self, id_usuario: str) -> None:
        self.activo = False
        self.registrar_modificacion(id_usuario)

    @abstractmethod
    def validar_identificacion(self) -> None: ...


@dataclass(kw_only=True)
class PersonaNatural(Contratista):
    tipo_persona: ClassVar[TipoPersona] = TipoPersona.NATURAL

    def validar_identificacion(self) -> None:
        if not PATRON_CEDULA.fullmatch(self.nit_cedula):
            raise ErrorDominio("La cédula debe ser numérica, de 6 a 10 dígitos y sin cero inicial")


@dataclass(kw_only=True)
class PersonaJuridica(Contratista):
    tipo_persona: ClassVar[TipoPersona] = TipoPersona.JURIDICA

    def validar_identificacion(self) -> None:
        coincidencia = PATRON_NIT.fullmatch(self.nit_cedula)
        if coincidencia is None:
            raise ErrorDominio("El NIT debe tener el formato NNNNNNNNN o NNNNNNNNN-D")
        numero, digito = coincidencia.groups()
        if digito is not None and digito_verificacion_nit(numero) != int(digito):
            raise ErrorDominio("El dígito de verificación del NIT no es válido")
