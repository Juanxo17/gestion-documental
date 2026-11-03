from dataclasses import dataclass
from decimal import Decimal

from gestion_documental.domain.errores import ErrorDominio

CENTAVOS = Decimal("0.01")


@dataclass(frozen=True)
class ValorMonetario:
    monto: Decimal

    def __post_init__(self) -> None:
        if not isinstance(self.monto, Decimal):
            raise ErrorDominio("El valor monetario debe ser Decimal, no float ni int")
        if not self.monto.is_finite() or self.monto <= 0:
            raise ErrorDominio("El valor monetario debe ser mayor que cero")
        if self.monto != self.monto.quantize(CENTAVOS):
            raise ErrorDominio("El valor monetario admite máximo dos decimales")
