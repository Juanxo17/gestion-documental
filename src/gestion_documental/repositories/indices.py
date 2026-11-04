from pymongo import ASCENDING, IndexModel
from pymongo.database import Database

from gestion_documental.repositories.mapeo import (
    COLECCION_CONTRATISTAS,
    COLECCION_CONTRATOS,
    COLECCION_CUENTAS,
    COLECCION_ROLES,
    COLECCION_USUARIOS,
    Registro,
)

INDICES: dict[str, list[IndexModel]] = {
    COLECCION_ROLES: [IndexModel("nombre", unique=True, name="uq_roles_nombre")],
    COLECCION_USUARIOS: [IndexModel("correo", unique=True, name="uq_usuarios_correo")],
    COLECCION_CONTRATISTAS: [
        IndexModel("nit_cedula", unique=True, name="uq_contratistas_nit_cedula"),
    ],
    COLECCION_CONTRATOS: [
        IndexModel("numero_contrato", unique=True, name="uq_contratos_numero"),
        IndexModel("id_contratista", name="idx_contratos_id_contratista"),
    ],
    COLECCION_CUENTAS: [
        IndexModel("numero_radicado", unique=True, name="uq_cuentas_cobro_radicado"),
        IndexModel(
            [("id_contrato", ASCENDING), ("numero_cuenta", ASCENDING)],
            unique=True,
            name="uq_cuentas_cobro_contrato_cuenta",
        ),
        IndexModel("estado", name="idx_cuentas_cobro_estado"),
    ],
}


def crear_indices(db: Database[Registro]) -> None:
    for coleccion, indices in INDICES.items():
        db[coleccion].create_indexes(indices)
