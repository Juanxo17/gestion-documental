from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.events.auditoria import AuditoriaPersistente

ESTADOS_SIN_COMPROMISO = frozenset({EstadoCuenta.ANULADA, EstadoCuenta.RECHAZADA})


class RegistroDuplicadoError(Exception):
    pass


@dataclass(frozen=True, kw_only=True)
class FiltroCuentas:
    estado: EstadoCuenta | None = None
    ids_contrato: tuple[str, ...] | None = None
    desde: date | None = None
    hasta: date | None = None

    def admite(self, cuenta: CuentaCobro) -> bool:
        return (
            (self.estado is None or cuenta.estado is self.estado)
            and (self.ids_contrato is None or cuenta.id_contrato in self.ids_contrato)
            and (self.desde is None or cuenta.fecha_presentacion >= self.desde)
            and (self.hasta is None or cuenta.fecha_presentacion <= self.hasta)
        )


@dataclass(frozen=True)
class ResumenGrupo:
    clave: str
    cantidad: int
    total: Decimal


class RepositorioCuentas(ABC):
    @abstractmethod
    def guardar(self, cuenta: CuentaCobro) -> None: ...

    @abstractmethod
    def obtener_por_radicado(self, numero_radicado: str) -> CuentaCobro | None: ...

    @abstractmethod
    def listar_por_estado(self, estado: EstadoCuenta) -> list[CuentaCobro]: ...

    @abstractmethod
    def existe_numero_cuenta(self, id_contrato: str, numero_cuenta: str) -> bool: ...

    @abstractmethod
    def buscar(
        self, filtro: FiltroCuentas, pagina: int, tamano: int
    ) -> tuple[list[CuentaCobro], int]: ...

    @abstractmethod
    def suma_comprometida(
        self, id_contrato: str, excluir_radicado: str | None = None
    ) -> Decimal: ...

    @abstractmethod
    def resumen_por_estado(self) -> list[ResumenGrupo]: ...

    @abstractmethod
    def resumen_por_contrato(self) -> list[ResumenGrupo]: ...


class RepositorioContratos(ABC):
    @abstractmethod
    def obtener_por_numero(self, numero_contrato: str) -> Contrato | None: ...

    @abstractmethod
    def obtener_por_id(self, id_contrato: str) -> Contrato | None: ...

    @abstractmethod
    def listar(
        self, id_contratista: str | None = None, estado: EstadoContrato | None = None
    ) -> list[Contrato]: ...

    @abstractmethod
    def guardar(self, contrato: Contrato) -> None: ...


class RepositorioContratistas(ABC):
    @abstractmethod
    def obtener_por_identificacion(self, nit_cedula: str) -> Contratista | None: ...

    @abstractmethod
    def obtener_por_id(self, id_contratista: str) -> Contratista | None: ...

    @abstractmethod
    def buscar(self, texto: str | None = None, solo_activos: bool = False) -> list[Contratista]: ...

    @abstractmethod
    def guardar(self, contratista: Contratista) -> None: ...


class RepositorioUsuarios(ABC):
    @abstractmethod
    def obtener_por_id(self, id_usuario: str) -> Usuario | None: ...

    @abstractmethod
    def obtener_por_correo(self, correo: str) -> Usuario | None: ...

    @abstractmethod
    def listar(self) -> list[Usuario]: ...

    @abstractmethod
    def guardar(self, usuario: Usuario) -> None: ...


class RepositorioRoles(ABC):
    @abstractmethod
    def obtener_por_id(self, id_rol: str) -> Rol | None: ...

    @abstractmethod
    def obtener_por_nombre(self, nombre: str) -> Rol | None: ...

    @abstractmethod
    def listar(self) -> list[Rol]: ...


class RepositorioArchivos(ABC):
    @abstractmethod
    def guardar(self, nombre: str, contenido: bytes, tipo_mime: str) -> str: ...

    @abstractmethod
    def leer_bloques(self, id_archivo: str) -> Iterator[bytes]: ...

    @abstractmethod
    def eliminar(self, id_archivo: str) -> None: ...


@dataclass(frozen=True)
class Repositorios:
    cuentas: RepositorioCuentas
    contratos: RepositorioContratos
    contratistas: RepositorioContratistas
    usuarios: RepositorioUsuarios
    roles: RepositorioRoles
    archivos: RepositorioArchivos
    auditoria: AuditoriaPersistente
