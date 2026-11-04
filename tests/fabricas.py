from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

from gestion_documental.domain.contratistas import Contratista, PersonaJuridica, PersonaNatural
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento
from gestion_documental.domain.tiempo import ahora_utc
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.events.comandos import RadicarCuenta
from gestion_documental.events.eventos import (
    CuentaRadicada,
    DocumentoAdjuntado,
    EstadoCuentaCambiado,
    EventoDominio,
)
from gestion_documental.events.publicador import BusEventosEnMemoria
from gestion_documental.repositories.base import RepositorioCuentas, Repositorios
from gestion_documental.repositories.memoria import (
    RepositorioRolesEnMemoria,
    RepositorioUsuariosEnMemoria,
    repositorios_en_memoria,
)
from gestion_documental.services.servicio_auth import ServicioAuth
from gestion_documental.services.servicio_contratistas import ServicioContratistas
from gestion_documental.services.servicio_contratos import ServicioContratos
from gestion_documental.services.servicio_cuentas import ServicioCuentas
from gestion_documental.services.servicio_usuarios import ServicioUsuarios


def cuenta_radicada() -> CuentaRadicada:
    return CuentaRadicada(
        id_usuario="radicador-sintetico",
        numero_radicado="RAD-SINT-0001",
        id_contrato="contrato-sintetico-1",
        valor_cobro=Decimal("1500000.00"),
    )


def estado_cambiado(nuevo: EstadoCuenta = EstadoCuenta.APROBADA) -> EstadoCuentaCambiado:
    return EstadoCuentaCambiado(
        id_usuario="revisor-sintetico",
        numero_radicado="RAD-SINT-0001",
        estado_anterior=EstadoCuenta.EN_REVISION,
        estado_nuevo=nuevo,
    )


def documento_adjuntado() -> DocumentoAdjuntado:
    return DocumentoAdjuntado(
        id_usuario="radicador-sintetico",
        numero_radicado="RAD-SINT-0001",
        nombre_original="rut_sintetico.pdf",
        origen=OrigenDocumento.URL,
        tipo=TipoDocumento.RUT,
    )


def radicar() -> RadicarCuenta:
    return RadicarCuenta(
        id_usuario="radicador-sintetico",
        numero_radicado="RAD-SINT-0001",
        numero_cuenta="CUENTA-001",
        numero_contrato="CONT-SINT-001",
        valor_cobro=Decimal("1500000.00"),
        concepto_pago="Honorarios sintéticos",
        fecha_presentacion=date(2026, 1, 31),
    )


CONTRATO_ID = "64b000000000000000000001"
CONTRATISTA_ID = "64b000000000000000000002"
CONTRATISTA_INACTIVO_ID = "64b000000000000000000004"
USUARIO_ID = "64b0000000000000000000aa"


class Recolector:
    def __init__(self) -> None:
        self.eventos: list[EventoDominio] = []

    def manejar(self, evento: EventoDominio) -> None:
        self.eventos.append(evento)


def contrato_en_memoria() -> Contrato:
    return Contrato(
        id=CONTRATO_ID,
        numero_contrato="CONT-SINT-001",
        id_contratista=CONTRATISTA_ID,
        objeto_contrato="Objeto sintético",
        valor_total=ValorMonetario(Decimal("10000000.00")),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        id_supervisor="64b000000000000000000003",
    )


def contratistas_sinteticos() -> list[Contratista]:
    return [
        PersonaJuridica(
            id=CONTRATISTA_ID, nombre_completo="Empresa Sintética S.A.S.", nit_cedula="900000001-2"
        ),
        PersonaNatural(
            id=CONTRATISTA_INACTIVO_ID,
            nombre_completo="Persona Sintética Inactiva",
            nit_cedula="1000000001",
            activo=False,
        ),
    ]


def servicio_en_memoria(
    cuentas: RepositorioCuentas | None = None,
) -> tuple[ServicioCuentas, RepositorioCuentas, Recolector]:
    datos = escenario(cuentas)
    return datos.cuentas(), datos.repos.cuentas, datos.recolector


CONTRASENA = "Demo2025*"
SECRETO_PRUEBAS = "secreto-de-pruebas-con-mas-de-32-caracteres"
HASHER_RAPIDO = PasswordHash((BcryptHasher(rounds=4),))
TODOS_LOS_PERMISOS = [
    "usuarios.gestionar",
    "contratistas.gestionar",
    "contratistas.consultar",
    "contratos.gestionar",
    "contratos.consultar",
    "cuentas.radicar",
    "cuentas.consultar",
    "cuentas.editar",
    "cuentas.cambiar_estado",
    "cuentas.pagar",
    "documentos.adjuntar",
    "documentos.consultar",
    "documentos.eliminar",
]
PERMISOS_POR_ROL = {
    "Administrador": TODOS_LOS_PERMISOS,
    "Radicador": [TODOS_LOS_PERMISOS[i - 1] for i in (3, 5, 6, 7, 8, 11, 12, 13)],
    "Revisor": [TODOS_LOS_PERMISOS[i - 1] for i in (3, 5, 7, 9, 12)],
    "Supervisor": [TODOS_LOS_PERMISOS[i - 1] for i in (3, 4, 5, 7, 9, 12)],
    "Consulta": [TODOS_LOS_PERMISOS[i - 1] for i in (3, 5, 7, 12)],
}


def roles_sinteticos() -> list[Rol]:
    return [
        Rol(id=f"64c0000000000000000000{indice:02d}", nombre=nombre, descripcion=nombre,
            permisos=frozenset(permisos))
        for indice, (nombre, permisos) in enumerate(PERMISOS_POR_ROL.items(), start=1)
    ]  # fmt: skip


def usuarios_sinteticos(roles: list[Rol]) -> list[Usuario]:
    por_nombre = {rol.nombre: rol for rol in roles}
    contrasena_hash = HASHER_RAPIDO.hash(CONTRASENA)

    def crear(correo: str, rol: str, **cambios: Any) -> Usuario:
        datos: dict[str, Any] = {
            "nombre": correo.split("@")[0].capitalize(),
            "apellido": "Sintético",
            "correo": correo,
            "id_rol": por_nombre[rol].id,
            "cargo": rol,
            "contrasena_hash": contrasena_hash,
            "debe_cambiar_contrasena": False,
            **cambios,
        }
        return Usuario(**datos)

    return [
        *(crear(f"{nombre.lower()}@example.com", nombre) for nombre in PERMISOS_POR_ROL),
        crear("inactivo@example.com", "Consulta", activo=False),
        crear("nuevo@example.com", "Radicador", debe_cambiar_contrasena=True),
    ]


def servicio_auth_en_memoria(
    reloj: Callable[[], datetime] = ahora_utc,
) -> tuple[ServicioAuth, RepositorioUsuariosEnMemoria]:
    roles = roles_sinteticos()
    usuarios = RepositorioUsuariosEnMemoria(usuarios_sinteticos(roles))
    servicio = ServicioAuth(
        usuarios,
        RepositorioRolesEnMemoria(roles),
        secreto=SECRETO_PRUEBAS,
        minutos_token=30,
        hasher=HASHER_RAPIDO,
        reloj=reloj,
    )
    return servicio, usuarios


@dataclass
class Escenario:
    repos: Repositorios
    bus: BusEventosEnMemoria
    recolector: Recolector

    def usuario(self, correo: str) -> Usuario:
        usuario = self.repos.usuarios.obtener_por_correo(correo)
        assert usuario is not None
        return usuario

    def id_de(self, correo: str) -> str:
        identificador = self.usuario(correo).id
        assert identificador is not None
        return identificador

    def cuentas(self) -> ServicioCuentas:
        r = self.repos
        return ServicioCuentas(r.cuentas, r.contratos, r.contratistas, r.archivos, self.bus)

    def contratos(self) -> ServicioContratos:
        r = self.repos
        return ServicioContratos(
            r.contratos, r.contratistas, r.usuarios, r.roles, r.cuentas, self.bus
        )

    def contratistas(self) -> ServicioContratistas:
        return ServicioContratistas(self.repos.contratistas)

    def usuarios(self) -> ServicioUsuarios:
        return ServicioUsuarios(self.repos.usuarios, self.repos.roles, HASHER_RAPIDO)


def escenario(cuentas: RepositorioCuentas | None = None) -> Escenario:
    roles = roles_sinteticos()
    repos = repositorios_en_memoria(
        contratos=[contrato_en_memoria()],
        contratistas=contratistas_sinteticos(),
        usuarios=usuarios_sinteticos(roles),
        roles=roles,
        cuentas=cuentas,
    )
    bus = BusEventosEnMemoria()
    recolector = Recolector()
    bus.suscribir(EventoDominio, recolector)
    bus.suscribir(EventoDominio, repos.auditoria)
    return Escenario(repos=repos, bus=bus, recolector=recolector)
