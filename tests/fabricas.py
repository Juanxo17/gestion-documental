from datetime import date
from decimal import Decimal

from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento
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
)
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
