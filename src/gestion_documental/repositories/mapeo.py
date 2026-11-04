from datetime import UTC, date, datetime, time
from typing import Any

from bson import Decimal128, ObjectId

from gestion_documental.domain.contratistas import Contratista, PersonaJuridica, PersonaNatural
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CambioEstado, CuentaCobro
from gestion_documental.domain.documentos import (
    MIME_PDF,
    Documento,
    DocumentoLocal,
    DocumentoPDF,
    DocumentoURL,
)
from gestion_documental.domain.enums import (
    EstadoContrato,
    EstadoCuenta,
    OrigenDocumento,
    TipoDocumento,
    TipoPersona,
)
from gestion_documental.domain.valores import ValorMonetario

Registro = dict[str, Any]

COLECCION_ROLES = "roles"
COLECCION_USUARIOS = "usuarios"
COLECCION_CONTRATISTAS = "contratistas"
COLECCION_CONTRATOS = "contratos"
COLECCION_CUENTAS = "cuentas_cobro"
COLECCIONES = (
    COLECCION_ROLES,
    COLECCION_USUARIOS,
    COLECCION_CONTRATISTAS,
    COLECCION_CONTRATOS,
    COLECCION_CUENTAS,
)

CLASES_CONTRATISTA: dict[TipoPersona, type[Contratista]] = {
    TipoPersona.NATURAL: PersonaNatural,
    TipoPersona.JURIDICA: PersonaJuridica,
}


def id_opcional_a_bson(valor: str | None) -> ObjectId | None:
    return None if valor is None else ObjectId(valor)


def id_opcional_desde_bson(valor: ObjectId | None) -> str | None:
    return None if valor is None else str(valor)


def fecha_a_bson(valor: date) -> datetime:
    return datetime.combine(valor, time.min, tzinfo=UTC)


def dinero_a_bson(valor: ValorMonetario) -> Decimal128:
    return Decimal128(valor.monto)


def dinero_desde_bson(valor: Decimal128) -> ValorMonetario:
    return ValorMonetario(valor.to_decimal())


def documento_a_dict(documento: Documento) -> Registro:
    datos = documento.a_dict()
    del datos["descripcion"]
    datos["id_usuario"] = ObjectId(documento.id_usuario)
    return datos


def dict_a_documento(datos: Registro) -> Documento:
    comunes: Registro = {
        "nombre_original": datos["nombre_original"],
        "ruta_archivo": datos["ruta_archivo"],
        "tipo": TipoDocumento(datos["tipo"]),
        "id_usuario": str(datos["id_usuario"]),
        "fecha_carga": datos["fecha_carga"],
    }
    if datos["origen"] == OrigenDocumento.URL:
        return DocumentoURL(**comunes)
    clase = DocumentoPDF if datos["tipo_mime"] == MIME_PDF else DocumentoLocal
    return clase(
        **comunes,
        tipo_mime=datos["tipo_mime"],
        hash_sha256=datos["hash_sha256"],
        tamano_bytes=datos["tamano_bytes"],
    )


def cambio_a_dict(cambio: CambioEstado) -> Registro:
    return {
        "estado_anterior": None if cambio.estado_anterior is None else cambio.estado_anterior.value,
        "estado_nuevo": cambio.estado_nuevo.value,
        "id_usuario": ObjectId(cambio.id_usuario),
        "fecha_cambio": cambio.fecha_cambio,
        "observacion": cambio.observacion,
    }


def dict_a_cambio(datos: Registro) -> CambioEstado:
    anterior = datos["estado_anterior"]
    return CambioEstado(
        estado_anterior=None if anterior is None else EstadoCuenta(anterior),
        estado_nuevo=EstadoCuenta(datos["estado_nuevo"]),
        id_usuario=str(datos["id_usuario"]),
        fecha_cambio=datos["fecha_cambio"],
        observacion=datos["observacion"],
    )


def cuenta_a_dict(cuenta: CuentaCobro) -> Registro:
    return {
        "numero_radicado": cuenta.numero_radicado,
        "numero_cuenta": cuenta.numero_cuenta,
        "id_contrato": ObjectId(cuenta.id_contrato),
        "valor_cobro": dinero_a_bson(cuenta.valor_cobro),
        "concepto_pago": cuenta.concepto_pago,
        "fecha_presentacion": fecha_a_bson(cuenta.fecha_presentacion),
        "estado": cuenta.estado.value,
        "observaciones": cuenta.observaciones,
        "id_usuario": ObjectId(cuenta.id_usuario),
        "documentos": [documento_a_dict(documento) for documento in cuenta.documentos],
        "historial": [cambio_a_dict(cambio) for cambio in cuenta.historial],
    }


def dict_a_cuenta(datos: Registro) -> CuentaCobro:
    return CuentaCobro(
        numero_radicado=datos["numero_radicado"],
        numero_cuenta=datos["numero_cuenta"],
        id_contrato=str(datos["id_contrato"]),
        valor_cobro=dinero_desde_bson(datos["valor_cobro"]),
        concepto_pago=datos["concepto_pago"],
        fecha_presentacion=datos["fecha_presentacion"].date(),
        id_usuario=str(datos["id_usuario"]),
        observaciones=datos["observaciones"],
        documentos=[dict_a_documento(documento) for documento in datos["documentos"]],
        historial=[dict_a_cambio(cambio) for cambio in datos["historial"]],
    )


def contrato_a_dict(contrato: Contrato) -> Registro:
    datos: Registro = {
        "numero_contrato": contrato.numero_contrato,
        "id_contratista": ObjectId(contrato.id_contratista),
        "objeto_contrato": contrato.objeto_contrato,
        "valor_total": dinero_a_bson(contrato.valor_total),
        "fecha_inicio": fecha_a_bson(contrato.fecha_inicio),
        "fecha_fin": fecha_a_bson(contrato.fecha_fin),
        "estado": contrato.estado.value,
        "id_supervisor": ObjectId(contrato.id_supervisor),
    }
    if contrato.id is not None:
        datos["_id"] = ObjectId(contrato.id)
    return datos


def dict_a_contrato(datos: Registro) -> Contrato:
    return Contrato(
        id=str(datos["_id"]),
        numero_contrato=datos["numero_contrato"],
        id_contratista=str(datos["id_contratista"]),
        objeto_contrato=datos["objeto_contrato"],
        valor_total=dinero_desde_bson(datos["valor_total"]),
        fecha_inicio=datos["fecha_inicio"].date(),
        fecha_fin=datos["fecha_fin"].date(),
        estado=EstadoContrato(datos["estado"]),
        id_supervisor=str(datos["id_supervisor"]),
    )


def contratista_a_dict(contratista: Contratista) -> Registro:
    datos: Registro = {
        "tipo_persona": contratista.tipo_persona.value,
        "nombre_completo": contratista.nombre_completo,
        "nit_cedula": contratista.nit_cedula,
        "telefono": contratista.telefono,
        "correo": contratista.correo,
        "direccion": contratista.direccion,
        "activo": contratista.activo,
        "creado_por": id_opcional_a_bson(contratista.creado_por),
        "creado_en": contratista.creado_en,
        "modificado_por": id_opcional_a_bson(contratista.modificado_por),
        "modificado_en": contratista.modificado_en,
    }
    if contratista.id is not None:
        datos["_id"] = ObjectId(contratista.id)
    return datos


def dict_a_contratista(datos: Registro) -> Contratista:
    clase = CLASES_CONTRATISTA[TipoPersona(datos["tipo_persona"])]
    return clase(
        id=str(datos["_id"]),
        nombre_completo=datos["nombre_completo"],
        nit_cedula=datos["nit_cedula"],
        telefono=datos["telefono"],
        correo=datos["correo"],
        direccion=datos["direccion"],
        activo=datos["activo"],
        creado_por=id_opcional_desde_bson(datos["creado_por"]),
        creado_en=datos["creado_en"],
        modificado_por=id_opcional_desde_bson(datos["modificado_por"]),
        modificado_en=datos["modificado_en"],
    )
