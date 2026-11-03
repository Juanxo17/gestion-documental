from dataclasses import dataclass
from datetime import UTC, datetime

from gestion_documental.domain.errores import ErrorDominio


@dataclass(kw_only=True)
class AuditableMixin:
    creado_por: str | None = None
    creado_en: datetime | None = None
    modificado_por: str | None = None
    modificado_en: datetime | None = None

    def registrar_creacion(self, id_usuario: str) -> None:
        self.creado_por = id_usuario
        self.creado_en = datetime.now(UTC)

    def registrar_modificacion(self, id_usuario: str) -> None:
        if self.creado_por is None:
            raise ErrorDominio("No se puede registrar una modificación antes de la creación")
        self.modificado_por = id_usuario
        self.modificado_en = datetime.now(UTC)
