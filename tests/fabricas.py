from collections.abc import Callable
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher

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
from gestion_documental.repositories.base import RepositorioCuentas
from gestion_documental.repositories.memoria import (
    RepositorioContratosEnMemoria,
    RepositorioCuentasEnMemoria,
    RepositorioRolesEnMemoria,
    RepositorioUsuariosEnMemoria,
)
from gestion_documental.services.servicio_auth import ServicioAuth
from gestion_documental.services.servicio_cuentas import ServicioCuentas


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
        id_contratista="64b000000000000000000002",
        objeto_contrato="Objeto sintético",
        valor_total=ValorMonetario(Decimal("10000000.00")),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        id_supervisor="64b000000000000000000003",
    )


def servicio_en_memoria(
    cuentas: RepositorioCuentas | None = None,
) -> tuple[ServicioCuentas, RepositorioCuentas, Recolector]:
    repositorio = cuentas if cuentas is not None else RepositorioCuentasEnMemoria()
    bus = BusEventosEnMemoria()
    recolector = Recolector()
    bus.suscribir(EventoDominio, recolector)
    servicio = ServicioCuentas(
        repositorio, RepositorioContratosEnMemoria([contrato_en_memoria()]), bus
    )
    return servicio, repositorio, recolector


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
