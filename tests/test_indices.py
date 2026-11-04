from typing import Any

import pytest
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from gestion_documental.repositories.indices import INDICES
from gestion_documental.repositories.mapeo import COLECCION_CUENTAS

pytestmark = pytest.mark.integracion


def test_indices_creados(db_pruebas: Database[dict[str, Any]]) -> None:
    for coleccion, indices in INDICES.items():
        existentes = set(db_pruebas[coleccion].index_information())
        assert {indice.document["name"] for indice in indices} <= existentes


def test_indice_unico_rechaza_radicado_duplicado(db_pruebas: Database[dict[str, Any]]) -> None:
    cuentas = db_pruebas[COLECCION_CUENTAS]
    cuentas.insert_one({"numero_radicado": "RAD-DUP", "id_contrato": 1, "numero_cuenta": "A"})

    with pytest.raises(DuplicateKeyError):
        cuentas.insert_one({"numero_radicado": "RAD-DUP", "id_contrato": 2, "numero_cuenta": "B"})


def test_indice_compuesto_rechaza_cuenta_repetida_en_contrato(
    db_pruebas: Database[dict[str, Any]],
) -> None:
    cuentas = db_pruebas[COLECCION_CUENTAS]
    cuentas.insert_one({"numero_radicado": "RAD-1", "id_contrato": 1, "numero_cuenta": "A"})
    cuentas.insert_one({"numero_radicado": "RAD-2", "id_contrato": 2, "numero_cuenta": "A"})

    with pytest.raises(DuplicateKeyError):
        cuentas.insert_one({"numero_radicado": "RAD-3", "id_contrato": 1, "numero_cuenta": "A"})
