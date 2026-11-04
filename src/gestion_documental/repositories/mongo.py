import re
from collections.abc import Iterator
from decimal import Decimal
from typing import Any

from bson import ObjectId
from gridfs import GridFS
from gridfs.errors import NoFile
from pymongo import DESCENDING
from pymongo.collection import Collection
from pymongo.database import Database
from pymongo.errors import DuplicateKeyError

from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta
from gestion_documental.domain.errores import NoEncontradoError
from gestion_documental.domain.tiempo import ahora_utc
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.events.auditoria import (
    AuditoriaPersistente,
    FiltroAuditoria,
    RegistroEvento,
)
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
from gestion_documental.repositories.mapeo import (
    COLECCION_AUDITORIA,
    COLECCION_CONTRATISTAS,
    COLECCION_CONTRATOS,
    COLECCION_CUENTAS,
    COLECCION_ROLES,
    COLECCION_USUARIOS,
    Registro,
    contratista_a_dict,
    contrato_a_dict,
    cuenta_a_dict,
    dict_a_contratista,
    dict_a_contrato,
    dict_a_cuenta,
    dict_a_registro,
    dict_a_rol,
    dict_a_usuario,
    fecha_a_bson,
    registro_a_dict,
    usuario_a_dict,
)

TAMANO_BLOQUE = 255 * 1024


def buscar_por_id(coleccion: Collection[Registro], identificador: str) -> Registro | None:
    if not ObjectId.is_valid(identificador):
        return None
    return coleccion.find_one({"_id": ObjectId(identificador)})


def reemplazar(coleccion: Collection[Registro], datos: Registro, mensaje_duplicado: str) -> None:
    try:
        coleccion.replace_one({"_id": datos["_id"]}, datos, upsert=True)
    except DuplicateKeyError as exc:
        raise RegistroDuplicadoError(mensaje_duplicado) from exc


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

    def buscar(
        self, filtro: FiltroCuentas, pagina: int, tamano: int
    ) -> tuple[list[CuentaCobro], int]:
        consulta: Registro = {}
        if filtro.estado is not None:
            consulta["estado"] = filtro.estado.value
        if filtro.ids_contrato is not None:
            consulta["id_contrato"] = {"$in": [ObjectId(id_) for id_ in filtro.ids_contrato]}
        rango: Registro = {}
        if filtro.desde is not None:
            rango["$gte"] = fecha_a_bson(filtro.desde)
        if filtro.hasta is not None:
            rango["$lte"] = fecha_a_bson(filtro.hasta)
        if rango:
            consulta["fecha_presentacion"] = rango
        total = self._coleccion.count_documents(consulta)
        cursor = (
            self._coleccion.find(consulta)
            .sort("numero_radicado")
            .skip((pagina - 1) * tamano)
            .limit(tamano)
        )
        return [dict_a_cuenta(datos) for datos in cursor], total

    def suma_comprometida(self, id_contrato: str, excluir_radicado: str | None = None) -> Decimal:
        coincidencia: Registro = {
            "id_contrato": ObjectId(id_contrato),
            "estado": {"$nin": [estado.value for estado in ESTADOS_SIN_COMPROMISO]},
        }
        if excluir_radicado is not None:
            coincidencia["numero_radicado"] = {"$ne": excluir_radicado}
        resultado = list(
            self._coleccion.aggregate(
                [
                    {"$match": coincidencia},
                    {"$group": {"_id": None, "total": {"$sum": "$valor_cobro"}}},
                ]
            )
        )
        return resultado[0]["total"].to_decimal() if resultado else Decimal(0)

    def resumen_por_estado(self) -> list[ResumenGrupo]:
        return self._agrupar("$estado")

    def resumen_por_contrato(self) -> list[ResumenGrupo]:
        return self._agrupar("$id_contrato")

    def _agrupar(self, campo: str) -> list[ResumenGrupo]:
        cursor = self._coleccion.aggregate(
            [
                {
                    "$group": {
                        "_id": campo,
                        "cantidad": {"$sum": 1},
                        "total": {"$sum": "$valor_cobro"},
                    }
                },
                {"$sort": {"_id": 1}},
            ]
        )
        return [
            ResumenGrupo(
                clave=str(grupo["_id"]),
                cantidad=grupo["cantidad"],
                total=grupo["total"].to_decimal(),
            )
            for grupo in cursor
        ]


class RepositorioContratosMongo(RepositorioContratos):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_CONTRATOS]

    def obtener_por_numero(self, numero_contrato: str) -> Contrato | None:
        datos = self._coleccion.find_one({"numero_contrato": numero_contrato})
        return None if datos is None else dict_a_contrato(datos)

    def obtener_por_id(self, id_contrato: str) -> Contrato | None:
        datos = buscar_por_id(self._coleccion, id_contrato)
        return None if datos is None else dict_a_contrato(datos)

    def listar(
        self, id_contratista: str | None = None, estado: EstadoContrato | None = None
    ) -> list[Contrato]:
        consulta: Registro = {}
        if id_contratista is not None:
            consulta["id_contratista"] = ObjectId(id_contratista)
        if estado is not None:
            consulta["estado"] = estado.value
        cursor = self._coleccion.find(consulta).sort("numero_contrato")
        return [dict_a_contrato(datos) for datos in cursor]

    def guardar(self, contrato: Contrato) -> None:
        if contrato.id is None:
            contrato.id = str(ObjectId())
        reemplazar(
            self._coleccion,
            contrato_a_dict(contrato),
            f"Ya existe el contrato {contrato.numero_contrato}",
        )


class RepositorioContratistasMongo(RepositorioContratistas):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_CONTRATISTAS]

    def obtener_por_identificacion(self, nit_cedula: str) -> Contratista | None:
        datos = self._coleccion.find_one({"nit_cedula": nit_cedula})
        return None if datos is None else dict_a_contratista(datos)

    def obtener_por_id(self, id_contratista: str) -> Contratista | None:
        datos = buscar_por_id(self._coleccion, id_contratista)
        return None if datos is None else dict_a_contratista(datos)

    def buscar(self, texto: str | None = None, solo_activos: bool = False) -> list[Contratista]:
        consulta: Registro = {}
        if texto and texto.strip():
            patron = re.escape(texto.strip())
            consulta["$or"] = [
                {"nombre_completo": {"$regex": patron, "$options": "i"}},
                {"nit_cedula": {"$regex": f"^{patron}"}},
            ]
        if solo_activos:
            consulta["activo"] = True
        cursor = self._coleccion.find(consulta).sort("nombre_completo")
        return [dict_a_contratista(datos) for datos in cursor]

    def guardar(self, contratista: Contratista) -> None:
        if contratista.id is None:
            contratista.id = str(ObjectId())
        reemplazar(
            self._coleccion,
            contratista_a_dict(contratista),
            f"Ya existe un contratista con identificación {contratista.nit_cedula}",
        )


class RepositorioUsuariosMongo(RepositorioUsuarios):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_USUARIOS]

    def obtener_por_id(self, id_usuario: str) -> Usuario | None:
        datos = buscar_por_id(self._coleccion, id_usuario)
        return None if datos is None else dict_a_usuario(datos)

    def obtener_por_correo(self, correo: str) -> Usuario | None:
        datos = self._coleccion.find_one({"correo": correo})
        return None if datos is None else dict_a_usuario(datos)

    def listar(self) -> list[Usuario]:
        return [dict_a_usuario(datos) for datos in self._coleccion.find().sort("correo")]

    def guardar(self, usuario: Usuario) -> None:
        if usuario.id is None:
            usuario.id = str(ObjectId())
        reemplazar(
            self._coleccion,
            usuario_a_dict(usuario),
            f"Ya existe un usuario con correo {usuario.correo}",
        )


class RepositorioRolesMongo(RepositorioRoles):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_ROLES]

    def obtener_por_id(self, id_rol: str) -> Rol | None:
        datos = buscar_por_id(self._coleccion, id_rol)
        return None if datos is None else dict_a_rol(datos)

    def obtener_por_nombre(self, nombre: str) -> Rol | None:
        datos = self._coleccion.find_one({"nombre": nombre})
        return None if datos is None else dict_a_rol(datos)

    def listar(self) -> list[Rol]:
        return [dict_a_rol(datos) for datos in self._coleccion.find().sort("nombre")]


class RepositorioArchivosGridFS(RepositorioArchivos):
    def __init__(self, db: Database[Registro]) -> None:
        self._fs = GridFS(db)

    def guardar(self, nombre: str, contenido: bytes, tipo_mime: str) -> str:
        return str(self._fs.put(contenido, filename=nombre, metadata={"tipo_mime": tipo_mime}))

    def leer_bloques(self, id_archivo: str) -> Iterator[bytes]:
        if not ObjectId.is_valid(id_archivo):
            raise NoEncontradoError(f"No existe el archivo {id_archivo}")
        try:
            archivo = self._fs.get(ObjectId(id_archivo))
        except NoFile as exc:
            raise NoEncontradoError(f"No existe el archivo {id_archivo}") from exc

        def bloques() -> Iterator[bytes]:
            while bloque := archivo.read(TAMANO_BLOQUE):
                yield bloque

        return bloques()

    def eliminar(self, id_archivo: str) -> None:
        if ObjectId.is_valid(id_archivo):
            self._fs.delete(ObjectId(id_archivo))


class AuditoriaMongo(AuditoriaPersistente):
    def __init__(self, db: Database[Registro]) -> None:
        self._coleccion = db[COLECCION_AUDITORIA]

    def registrar(self, registro: RegistroEvento) -> None:
        self._coleccion.insert_one(registro_a_dict(registro))

    def buscar(self, filtro: FiltroAuditoria) -> list[RegistroEvento]:
        consulta: dict[str, Any] = {}
        if filtro.tipo is not None:
            consulta["tipo"] = filtro.tipo
        if filtro.id_usuario is not None:
            consulta["id_usuario"] = filtro.id_usuario
        rango: dict[str, Any] = {}
        if filtro.desde is not None:
            rango["$gte"] = filtro.desde
        if filtro.hasta is not None:
            rango["$lte"] = filtro.hasta
        if rango:
            consulta["ocurrido_en"] = rango
        cursor = self._coleccion.find(consulta).sort("ocurrido_en", DESCENDING).limit(filtro.limite)
        return [dict_a_registro(datos) for datos in cursor]


def repositorios_mongo(db: Database[Registro]) -> Repositorios:
    return Repositorios(
        cuentas=RepositorioCuentasMongo(db),
        contratos=RepositorioContratosMongo(db),
        contratistas=RepositorioContratistasMongo(db),
        usuarios=RepositorioUsuariosMongo(db),
        roles=RepositorioRolesMongo(db),
        archivos=RepositorioArchivosGridFS(db),
        auditoria=AuditoriaMongo(db),
    )
