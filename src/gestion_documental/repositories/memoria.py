from collections.abc import Iterable
from copy import deepcopy

from bson import ObjectId

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.repositories.base import (
    RegistroDuplicadoError,
    RepositorioContratistas,
    RepositorioContratos,
    RepositorioCuentas,
    RepositorioRoles,
    RepositorioUsuarios,
)


class RepositorioCuentasEnMemoria(RepositorioCuentas):
    def __init__(self) -> None:
        self._cuentas: dict[str, CuentaCobro] = {}

    def guardar(self, cuenta: CuentaCobro) -> None:
        for otra in self._cuentas.values():
            if otra.numero_radicado != cuenta.numero_radicado and (
                otra.id_contrato,
                otra.numero_cuenta,
            ) == (cuenta.id_contrato, cuenta.numero_cuenta):
                raise RegistroDuplicadoError(
                    f"Ya existe la cuenta {cuenta.numero_cuenta} "
                    f"en el contrato {cuenta.id_contrato}"
                )
        self._cuentas[cuenta.numero_radicado] = deepcopy(cuenta)

    def obtener_por_radicado(self, numero_radicado: str) -> CuentaCobro | None:
        cuenta = self._cuentas.get(numero_radicado)
        return None if cuenta is None else deepcopy(cuenta)

    def listar_por_estado(self, estado: EstadoCuenta) -> list[CuentaCobro]:
        return [
            deepcopy(self._cuentas[radicado])
            for radicado in sorted(self._cuentas)
            if self._cuentas[radicado].estado is estado
        ]

    def existe_numero_cuenta(self, id_contrato: str, numero_cuenta: str) -> bool:
        return any(
            cuenta.id_contrato == id_contrato and cuenta.numero_cuenta == numero_cuenta
            for cuenta in self._cuentas.values()
        )


class RepositorioContratosEnMemoria(RepositorioContratos):
    def __init__(self, contratos: Iterable[Contrato] = ()) -> None:
        self._contratos = {contrato.numero_contrato: deepcopy(contrato) for contrato in contratos}

    def obtener_por_numero(self, numero_contrato: str) -> Contrato | None:
        contrato = self._contratos.get(numero_contrato)
        return None if contrato is None else deepcopy(contrato)


class RepositorioContratistasEnMemoria(RepositorioContratistas):
    def __init__(self, contratistas: Iterable[Contratista] = ()) -> None:
        self._contratistas = {
            contratista.nit_cedula: deepcopy(contratista) for contratista in contratistas
        }

    def obtener_por_identificacion(self, nit_cedula: str) -> Contratista | None:
        contratista = self._contratistas.get(nit_cedula)
        return None if contratista is None else deepcopy(contratista)


class RepositorioUsuariosEnMemoria(RepositorioUsuarios):
    def __init__(self, usuarios: Iterable[Usuario] = ()) -> None:
        self._usuarios: dict[str, Usuario] = {}
        for usuario in usuarios:
            self.guardar(usuario)

    def obtener_por_id(self, id_usuario: str) -> Usuario | None:
        usuario = self._usuarios.get(id_usuario)
        return None if usuario is None else deepcopy(usuario)

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        for usuario in self._usuarios.values():
            if usuario.correo == correo:
                return deepcopy(usuario)
        return None

    def guardar(self, usuario: Usuario) -> None:
        if usuario.id is None:
            usuario.id = str(ObjectId())
        for otro in self._usuarios.values():
            if otro.correo == usuario.correo and otro.id != usuario.id:
                raise RegistroDuplicadoError(f"Ya existe un usuario con correo {usuario.correo}")
        self._usuarios[usuario.id] = deepcopy(usuario)


class RepositorioRolesEnMemoria(RepositorioRoles):
    def __init__(self, roles: Iterable[Rol] = ()) -> None:
        self._roles = {rol.id: deepcopy(rol) for rol in roles if rol.id is not None}

    def obtener_por_id(self, id_rol: str) -> Rol | None:
        rol = self._roles.get(id_rol)
        return None if rol is None else deepcopy(rol)
