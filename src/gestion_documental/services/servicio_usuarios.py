import secrets

from pwdlib import PasswordHash

from gestion_documental.domain.errores import ErrorDominio, NoEncontradoError
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.repositories.base import RepositorioRoles, RepositorioUsuarios


class ServicioUsuarios:
    def __init__(
        self, usuarios: RepositorioUsuarios, roles: RepositorioRoles, hasher: PasswordHash
    ) -> None:
        self._usuarios = usuarios
        self._roles = roles
        self._hasher = hasher

    def listar(self) -> list[Usuario]:
        return self._usuarios.listar()

    def obtener(self, id_usuario: str) -> Usuario:
        usuario = self._usuarios.obtener_por_id(id_usuario)
        if usuario is None:
            raise NoEncontradoError(f"No existe el usuario {id_usuario}")
        return usuario

    def rol(self, id_rol: str) -> Rol:
        rol = self._roles.obtener_por_id(id_rol)
        if rol is None:
            raise NoEncontradoError(f"No existe el rol {id_rol}")
        return rol

    def crear(
        self, *, nombre: str, apellido: str, correo: str, cargo: str, rol: str
    ) -> tuple[Usuario, str]:
        contrasena_temporal = secrets.token_urlsafe(9)
        usuario = Usuario(
            nombre=nombre,
            apellido=apellido,
            correo=correo.strip().lower(),
            id_rol=self._rol_por_nombre(rol),
            cargo=cargo,
            contrasena_hash=self._hasher.hash(contrasena_temporal),
            debe_cambiar_contrasena=True,
        )
        self._usuarios.guardar(usuario)
        return usuario, contrasena_temporal

    def editar(
        self,
        id_usuario: str,
        *,
        nombre: str | None = None,
        apellido: str | None = None,
        correo: str | None = None,
        cargo: str | None = None,
    ) -> Usuario:
        usuario = self.obtener(id_usuario)
        usuario.nombre = nombre or usuario.nombre
        usuario.apellido = apellido or usuario.apellido
        usuario.correo = correo.strip().lower() if correo else usuario.correo
        usuario.cargo = cargo or usuario.cargo
        usuario.validar()
        self._usuarios.guardar(usuario)
        return usuario

    def cambiar_rol(self, id_usuario: str, rol: str) -> Usuario:
        usuario = self.obtener(id_usuario)
        usuario.id_rol = self._rol_por_nombre(rol)
        self._usuarios.guardar(usuario)
        return usuario

    def desactivar(self, id_usuario: str, id_actor: str) -> Usuario:
        if id_usuario == id_actor:
            raise ErrorDominio("Un usuario no puede desactivarse a sí mismo")
        usuario = self.obtener(id_usuario)
        usuario.desactivar()
        self._usuarios.guardar(usuario)
        return usuario

    def reiniciar_bloqueo(self, id_usuario: str) -> Usuario:
        usuario = self.obtener(id_usuario)
        usuario.reiniciar_bloqueo()
        self._usuarios.guardar(usuario)
        return usuario

    def _rol_por_nombre(self, nombre: str) -> str:
        rol = self._roles.obtener_por_nombre(nombre)
        if rol is None or rol.id is None:
            raise NoEncontradoError(f"No existe el rol {nombre}")
        return rol.id
