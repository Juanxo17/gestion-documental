from dataclasses import dataclass
from datetime import datetime

from gestion_documental.domain.errores import ErrorDominio
from gestion_documental.domain.tiempo import ahora_utc


@dataclass(kw_only=True)
class AuditableMixin:
    creado_por: str | None = None
    creado_en: datetime | None = None
    modificado_por: str | None = None
    modificado_en: datetime | None = None

    def registrar_creacion(self, id_usuario: str) -> None:
        self.creado_por = id_usuario
        self.creado_en = ahora_utc()

    def registrar_modificacion(self, id_usuario: str) -> None:
        if self.creado_por is None:
            raise ErrorDominio("No se puede registrar una modificación antes de la creación")
        self.modificado_por = id_usuario
        self.modificado_en = ahora_utc()
