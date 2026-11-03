from datetime import date
from decimal import Decimal

from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento
from gestion_documental.events.comandos import RadicarCuenta
from gestion_documental.events.eventos import (
    CuentaRadicada,
    DocumentoAdjuntado,
    EstadoCuentaCambiado,
)


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
        id_contrato="contrato-sintetico-1",
        valor_cobro=Decimal("1500000.00"),
        concepto_pago="Honorarios sintéticos",
        fecha_presentacion=date(2026, 1, 31),
    )
