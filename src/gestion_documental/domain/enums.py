from enum import StrEnum


class OrigenDocumento(StrEnum):
    LOCAL = "LOCAL"
    URL = "URL"


class TipoDocumento(StrEnum):
    CUENTA_COBRO = "CUENTA_COBRO"
    CERTIFICADO = "CERTIFICADO"
    RUT = "RUT"
    CEDULA = "CEDULA"
    POLIZA = "POLIZA"
    OTRO = "OTRO"


class EstadoCuenta(StrEnum):
    RECIBIDA = "RECIBIDA"
    EN_REVISION = "EN_REVISION"
    APROBADA = "APROBADA"
    RECHAZADA = "RECHAZADA"
    PAGADA = "PAGADA"
    ANULADA = "ANULADA"


class EstadoContrato(StrEnum):
    ACTIVO = "ACTIVO"
    SUSPENDIDO = "SUSPENDIDO"
    LIQUIDADO = "LIQUIDADO"
    TERMINADO = "TERMINADO"
    CANCELADO = "CANCELADO"


class TipoPersona(StrEnum):
    NATURAL = "NATURAL"
    JURIDICA = "JURIDICA"
