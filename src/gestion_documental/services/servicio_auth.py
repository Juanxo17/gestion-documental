from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from gestion_documental.domain.errores import AccesoDenegadoError, ErrorDominio
from gestion_documental.domain.tiempo import ahora_utc
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.repositories.base import RepositorioRoles, RepositorioUsuarios

ALGORITMO_JWT = "HS256"
LONGITUD_MINIMA_CONTRASENA = 8


class CredencialesInvalidasError(Exception):
    pass


class PermisoDenegadoError(AccesoDenegadoError):
    pass


class CambioContrasenaRequeridoError(AccesoDenegadoError):
    pass


@dataclass(frozen=True)
class Sesion:
    usuario: Usuario
    rol: Rol

    @property
    def id_usuario(self) -> str:
        assert self.usuario.id is not None
        return self.usuario.id

    def exigir_permiso(self, codigo: str) -> None:
        if not self.rol.tiene_permiso(codigo):
            raise PermisoDenegadoError(f"El rol {self.rol.nombre} no tiene el permiso {codigo}")


def hasher_por_defecto() -> PasswordHash:
    return PasswordHash((BcryptHasher(),))


class ServicioAuth:
    def __init__(
        self,
        usuarios: RepositorioUsuarios,
        roles: RepositorioRoles,
        secreto: str,
        minutos_token: int,
        hasher: PasswordHash | None = None,
        reloj: Callable[[], datetime] = ahora_utc,
    ) -> None:
        self._usuarios = usuarios
        self._roles = roles
        self._secreto = secreto
        self._duracion_token = timedelta(minutes=minutos_token)
        self._hasher = hasher if hasher is not None else hasher_por_defecto()
        self._reloj = reloj

    def hashear(self, contrasena: str) -> str:
        return self._hasher.hash(contrasena)

    def login(self, correo: str, contrasena: str) -> str:
        usuario = self._usuarios.obtener_por_correo(correo.strip().lower())
        if usuario is None or usuario.id is None:
            raise CredencialesInvalidasError("Correo o contraseña incorrectos")
        ahora = self._reloj()
        usuario.verificar_bloqueo(ahora)
        if not self._hasher.verify(contrasena, usuario.contrasena_hash):
            usuario.registrar_login_fallido(ahora)
            self._usuarios.guardar(usuario)
            raise CredencialesInvalidasError("Correo o contraseña incorrectos")
        usuario.verificar_activo()
        usuario.registrar_login_exitoso(ahora)
        self._usuarios.guardar(usuario)
        return jwt.encode(
            {"sub": usuario.id, "iat": ahora, "exp": ahora + self._duracion_token},
            self._secreto,
            algorithm=ALGORITMO_JWT,
        )

    def sesion_desde_token(self, token: str) -> Sesion:
        try:
            datos = jwt.decode(token, self._secreto, algorithms=[ALGORITMO_JWT])
        except jwt.InvalidTokenError as exc:
            raise CredencialesInvalidasError("Token inválido o vencido") from exc
        usuario = self._usuarios.obtener_por_id(str(datos.get("sub", "")))
        if usuario is None:
            raise CredencialesInvalidasError("El usuario del token ya no existe")
        usuario.verificar_activo()
        return Sesion(usuario=usuario, rol=self._rol_de(usuario))

    def obtener_permisos(self, id_usuario: str) -> frozenset[str]:
        usuario = self._usuarios.obtener_por_id(id_usuario)
        if usuario is None:
            raise CredencialesInvalidasError("El usuario no existe")
        rol = self._rol_de(usuario)
        return rol.permisos if rol.activo else frozenset()

    def cambiar_contrasena(self, id_usuario: str, actual: str, nueva: str) -> None:
        usuario = self._usuarios.obtener_por_id(id_usuario)
        if usuario is None:
            raise CredencialesInvalidasError("El usuario no existe")
        if not self._hasher.verify(actual, usuario.contrasena_hash):
            raise ErrorDominio("La contraseña actual no es correcta")
        if len(nueva) < LONGITUD_MINIMA_CONTRASENA:
            raise ErrorDominio(
                f"La contraseña nueva debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres"
            )
        if nueva == actual:
            raise ErrorDominio("La contraseña nueva debe ser distinta de la actual")
        usuario.cambiar_contrasena(self._hasher.hash(nueva))
        self._usuarios.guardar(usuario)

    def _rol_de(self, usuario: Usuario) -> Rol:
        rol = self._roles.obtener_por_id(usuario.id_rol)
        if rol is None:
            raise AccesoDenegadoError("El usuario no tiene un rol válido")
        return rol
