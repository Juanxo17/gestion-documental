from bson import ObjectId
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoCuenta
from gestion_documental.domain.tiempo import ahora_utc
from gestion_documental.repositories.base import (
    RegistroDuplicadoError,
    RepositorioContratistas,
    RepositorioContratos,
    RepositorioCuentas,
)
from gestion_documental.repositories.mapeo import (
    COLECCION_CONTRATISTAS,
    COLECCION_CONTRATOS,
    COLECCION_CUENTAS,
    Registro,
    cuenta_a_dict,
    dict_a_contratista,
    dict_a_contrato,
    dict_a_cuenta,
)


class RepositorioCuentasMongo(RepositorioCuentas):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_CUENTAS]

    def guardar(self, cuenta: CuentaCobro) -> None:
        ahora = ahora_utc()
        try:
            self._coleccion.update_one(
                {"numero_radicado": cuenta.numero_radicado},
                {
                    "$set": {**cuenta_a_dict(cuenta), "fecha_actualizacion": ahora},
                    "$setOnInsert": {"fecha_registro": ahora},
                },
                upsert=True,
            )
        except DuplicateKeyError as exc:
            raise RegistroDuplicadoError(
                f"Ya existe la cuenta {cuenta.numero_cuenta} en el contrato {cuenta.id_contrato}"
            ) from exc

    def obtener_por_radicado(self, numero_radicado: str) -> CuentaCobro | None:
        datos = self._coleccion.find_one({"numero_radicado": numero_radicado})
        return None if datos is None else dict_a_cuenta(datos)

    def listar_por_estado(self, estado: EstadoCuenta) -> list[CuentaCobro]:
        cursor = self._coleccion.find({"estado": estado.value}).sort("numero_radicado")
        return [dict_a_cuenta(datos) for datos in cursor]

    def existe_numero_cuenta(self, id_contrato: str, numero_cuenta: str) -> bool:
        filtro = {"id_contrato": ObjectId(id_contrato), "numero_cuenta": numero_cuenta}
        return self._coleccion.count_documents(filtro, limit=1) > 0


class RepositorioContratosMongo(RepositorioContratos):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_CONTRATOS]

    def obtener_por_numero(self, numero_contrato: str) -> Contrato | None:
        datos = self._coleccion.find_one({"numero_contrato": numero_contrato})
        return None if datos is None else dict_a_contrato(datos)


class RepositorioContratistasMongo(RepositorioContratistas):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_CONTRATISTAS]

    def obtener_por_identificacion(self, nit_cedula: str) -> Contratista | None:
        datos = self._coleccion.find_one({"nit_cedula": nit_cedula})
        return None if datos is None else dict_a_contratista(datos)
