from dataclasses import dataclass, field
from datetime import datetime, timedelta

from gestion_documental.domain.errores import (
    ErrorDominio,
    UsuarioBloqueadoError,
    UsuarioInactivoError,
)
from gestion_documental.domain.tiempo import ahora_utc

MAXIMO_INTENTOS = 5
DURACION_BLOQUEO = timedelta(minutes=15)


@dataclass(kw_only=True)
class Rol:
    nombre: str
    descripcion: str
    permisos: frozenset[str]
    activo: bool = True
    id: str | None = None

    def __post_init__(self) -> None:
        if not self.nombre.strip():
            raise ErrorDominio("El rol necesita nombre")

    def tiene_permiso(self, codigo: str) -> bool:
        return self.activo and codigo in self.permisos


@dataclass(kw_only=True)
class Usuario:
    nombre: str
    apellido: str
    correo: str
    id_rol: str
    cargo: str
    contrasena_hash: str
    activo: bool = True
    ultimo_acceso: datetime | None = None
    intentos_fallidos: int = 0
    bloqueado_hasta: datetime | None = None
    debe_cambiar_contrasena: bool = True
    fecha_registro: datetime = field(default_factory=ahora_utc)
    id: str | None = None

    def __post_init__(self) -> None:
        if "@" not in self.correo:
            raise ErrorDominio("El correo del usuario no es válido")
        if self.intentos_fallidos < 0:
            raise ErrorDominio("intentos_fallidos no puede ser negativo")

    def esta_bloqueado(self, ahora: datetime) -> bool:
        return self.bloqueado_hasta is not None and ahora < self.bloqueado_hasta

    def verificar_bloqueo(self, ahora: datetime) -> None:
        if self.esta_bloqueado(ahora):
            raise UsuarioBloqueadoError(
                "Usuario bloqueado por intentos fallidos hasta "
                f"{self.bloqueado_hasta:%Y-%m-%d %H:%M} UTC"
            )

    def verificar_activo(self) -> None:
        if not self.activo:
            raise UsuarioInactivoError("El usuario está inactivo")

    def registrar_login_fallido(self, ahora: datetime) -> None:
        if self.bloqueado_hasta is not None and not self.esta_bloqueado(ahora):
            self.intentos_fallidos = 0
            self.bloqueado_hasta = None
        self.intentos_fallidos += 1
        if self.intentos_fallidos >= MAXIMO_INTENTOS:
            self.bloqueado_hasta = ahora + DURACION_BLOQUEO

    def registrar_login_exitoso(self, ahora: datetime) -> None:
        self.intentos_fallidos = 0
        self.bloqueado_hasta = None
        self.ultimo_acceso = ahora

    def cambiar_contrasena(self, nuevo_hash: str) -> None:
        self.contrasena_hash = nuevo_hash
        self.debe_cambiar_contrasena = False
