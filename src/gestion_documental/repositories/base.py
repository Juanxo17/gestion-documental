from abc import ABC, abstractmethod

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.domain.usuarios import Rol, Usuario


class RegistroDuplicadoError(Exception):
    pass


class RepositorioCuentas(ABC):
    @abstractmethod
    def guardar(self, cuenta: CuentaCobro) -> None: ...

    @abstractmethod
    def obtener_por_radicado(self, numero_radicado: str) -> CuentaCobro | None: ...

    @abstractmethod
    def listar_por_estado(self, estado: EstadoCuenta) -> list[CuentaCobro]: ...

    @abstractmethod
    def existe_numero_cuenta(self, id_contrato: str, numero_cuenta: str) -> bool: ...


class RepositorioContratos(ABC):
    @abstractmethod
    def obtener_por_numero(self, numero_contrato: str) -> Contrato | None: ...


class RepositorioContratistas(ABC):
    @abstractmethod
    def obtener_por_identificacion(self, nit_cedula: str) -> Contratista | None: ...


class RepositorioUsuarios(ABC):
    @abstractmethod
    def obtener_por_id(self, id_usuario: str) -> Usuario | None: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Usuario | None: ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None: ...


class RepositorioRoles(ABC):
    @abstractmethod
    def obtener_por_id(self, id_rol: str) -> Rol | None: ...
