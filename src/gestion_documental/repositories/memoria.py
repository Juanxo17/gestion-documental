from collections.abc import Callable, Iterable, Iterator
from copy import deepcopy
from decimal import Decimal

from bson import ObjectId

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta
from gestion_documental.domain.errores import NoEncontradoError
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.events.auditoria import AuditoriaEnMemoria
from gestion_documental.repositories.base import (
    ESTADOS_SIN_COMPROMISO,
    FiltroCuentas,
    RegistroDuplicadoError,
    RepositorioArchivos,
    RepositorioContratistas,
    RepositorioContratos,
    RepositorioCuentas,
    RepositorioRoles,
    Repositorios,
    RepositorioUsuarios,
    ResumenGrupo,
)

TAMANO_BLOQUE = 255 * 1024


def nuevo_id() -> str:
    return str(ObjectId())


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
        return self.buscar(FiltroCuentas(estado=estado), 1, len(self._cuentas) or 1)[0]

    def existe_numero_cuenta(self, id_contrato: str, numero_cuenta: str) -> bool:
        return any(
            cuenta.id_contrato == id_contrato and cuenta.numero_cuenta == numero_cuenta
            for cuenta in self._cuentas.values()
        )

    def buscar(
        self, filtro: FiltroCuentas, pagina: int, tamano: int
    ) -> tuple[list[CuentaCobro], int]:
        encontradas = [
            self._cuentas[radicado]
            for radicado in sorted(self._cuentas)
            if filtro.admite(self._cuentas[radicado])
        ]
        inicio = (pagina - 1) * tamano
        return deepcopy(encontradas[inicio : inicio + tamano]), len(encontradas)

    def suma_comprometida(self, id_contrato: str, excluir_radicado: str | None = None) -> Decimal:
        return sum(
            (
                cuenta.valor_cobro.monto
                for cuenta in self._cuentas.values()
                if cuenta.id_contrato == id_contrato
                and cuenta.estado not in ESTADOS_SIN_COMPROMISO
                and cuenta.numero_radicado != excluir_radicado
            ),
            Decimal(0),
        )

    def resumen_por_estado(self) -> list[ResumenGrupo]:
        return self._agrupar(lambda cuenta: cuenta.estado.value)

    def resumen_por_contrato(self) -> list[ResumenGrupo]:
        return self._agrupar(lambda cuenta: cuenta.id_contrato)

    def _agrupar(self, clave: Callable[[CuentaCobro], str]) -> list[ResumenGrupo]:
        grupos: dict[str, tuple[int, Decimal]] = {}
        for cuenta in self._cuentas.values():
            cantidad, total = grupos.get(clave(cuenta), (0, Decimal(0)))
            grupos[clave(cuenta)] = (cantidad + 1, total + cuenta.valor_cobro.monto)
        return [
            ResumenGrupo(clave=nombre, cantidad=cantidad, total=total)
            for nombre, (cantidad, total) in sorted(grupos.items())
        ]


class RepositorioContratosEnMemoria(RepositorioContratos):
    def __init__(self, contratos: Iterable[Contrato] = ()) -> None:
        self._contratos: dict[str, Contrato] = {}
        for contrato in contratos:
            self.guardar(contrato)

    def obtener_por_numero(self, numero_contrato: str) -> Contrato | None:
        for contrato in self._contratos.values():
            if contrato.numero_contrato == numero_contrato:
                return deepcopy(contrato)
        return None

    def obtener_por_id(self, id_contrato: str) -> Contrato | None:
        contrato = self._contratos.get(id_contrato)
        return None if contrato is None else deepcopy(contrato)

    def listar(
        self, id_contratista: str | None = None, estado: EstadoContrato | None = None
    ) -> list[Contrato]:
        return deepcopy(
            sorted(
                (
                    contrato
                    for contrato in self._contratos.values()
                    if (id_contratista is None or contrato.id_contratista == id_contratista)
                    and (estado is None or contrato.estado is estado)
                ),
                key=lambda contrato: contrato.numero_contrato,
            )
        )

    def guardar(self, contrato: Contrato) -> None:
        if contrato.id is None:
            contrato.id = nuevo_id()
        for otro in self._contratos.values():
            if otro.numero_contrato == contrato.numero_contrato and otro.id != contrato.id:
                raise RegistroDuplicadoError(f"Ya existe el contrato {contrato.numero_contrato}")
        self._contratos[contrato.id] = deepcopy(contrato)


class RepositorioContratistasEnMemoria(RepositorioContratistas):
    def __init__(self, contratistas: Iterable[Contratista] = ()) -> None:
        self._contratistas: dict[str, Contratista] = {}
        for contratista in contratistas:
            self.guardar(contratista)

    def obtener_por_identificacion(self, nit_cedula: str) -> Contratista | None:
        for contratista in self._contratistas.values():
            if contratista.nit_cedula == nit_cedula:
                return deepcopy(contratista)
        return None

    def obtener_por_id(self, id_contratista: str) -> Contratista | None:
        contratista = self._contratistas.get(id_contratista)
        return None if contratista is None else deepcopy(contratista)

    def buscar(self, texto: str | None = None, solo_activos: bool = False) -> list[Contratista]:
        consulta = (texto or "").strip().lower()
        return deepcopy(
            sorted(
                (
                    contratista
                    for contratista in self._contratistas.values()
                    if (not solo_activos or contratista.activo)
                    and (
                        consulta in contratista.nombre_completo.lower()
                        or contratista.nit_cedula.startswith(consulta)
                    )
                ),
                key=lambda contratista: contratista.nombre_completo,
            )
        )

    def guardar(self, contratista: Contratista) -> None:
        if contratista.id is None:
            contratista.id = nuevo_id()
        for otro in self._contratistas.values():
            if otro.nit_cedula == contratista.nit_cedula and otro.id != contratista.id:
                raise RegistroDuplicadoError(
                    f"Ya existe un contratista con identificación {contratista.nit_cedula}"
                )
        self._contratistas[contratista.id] = deepcopy(contratista)


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

    def listar(self) -> list[Usuario]:
        return deepcopy(sorted(self._usuarios.values(), key=lambda usuario: usuario.correo))

    def guardar(self, usuario: Usuario) -> None:
        if usuario.id is None:
            usuario.id = nuevo_id()
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

    def obtener_por_nombre(self, nombre: str) -> Rol | None:
        for rol in self._roles.values():
            if rol.nombre == nombre:
                return deepcopy(rol)
        return None

    def listar(self) -> list[Rol]:
        return deepcopy(sorted(self._roles.values(), key=lambda rol: rol.nombre))


class RepositorioArchivosEnMemoria(RepositorioArchivos):
    def __init__(self) -> None:
        self._archivos: dict[str, bytes] = {}

    def guardar(self, nombre: str, contenido: bytes, tipo_mime: str) -> str:
        id_archivo = nuevo_id()
        self._archivos[id_archivo] = contenido
        return id_archivo

    def leer_bloques(self, id_archivo: str) -> Iterator[bytes]:
        contenido = self._archivos.get(id_archivo)
        if contenido is None:
            raise NoEncontradoError(f"No existe el archivo {id_archivo}")
        return (
            contenido[inicio : inicio + TAMANO_BLOQUE]
            for inicio in range(0, len(contenido), TAMANO_BLOQUE)
        )

    def eliminar(self, id_archivo: str) -> None:
        self._archivos.pop(id_archivo, None)

    def existe(self, id_archivo: str) -> bool:
        return id_archivo in self._archivos

    def reemplazar(self, id_archivo: str, contenido: bytes) -> None:
        self._archivos[id_archivo] = contenido


def repositorios_en_memoria(
    *,
    contratos: Iterable[Contrato] = (),
    contratistas: Iterable[Contratista] = (),
    usuarios: Iterable[Usuario] = (),
    roles: Iterable[Rol] = (),
    cuentas: RepositorioCuentas | None = None,
) -> Repositorios:
    return Repositorios(
        cuentas=cuentas if cuentas is not None else RepositorioCuentasEnMemoria(),
        contratos=RepositorioContratosEnMemoria(contratos),
        contratistas=RepositorioContratistasEnMemoria(contratistas),
        usuarios=RepositorioUsuariosEnMemoria(usuarios),
        roles=RepositorioRolesEnMemoria(roles),
        archivos=RepositorioArchivosEnMemoria(),
        auditoria=AuditoriaEnMemoria(),
    )
