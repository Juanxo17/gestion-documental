from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from bson import ObjectId
from pymongo.database import Database

from gestion_documental.domain.contratistas import Contratista, PersonaJuridica, PersonaNatural
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.cuenta_cobro import CambioEstado, CuentaCobro
from gestion_documental.domain.documentos import Documento, DocumentoPDF, DocumentoURL
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta, TipoDocumento
from gestion_documental.domain.usuarios import Rol, Usuario
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.repositories.conexion import get_db
from gestion_documental.repositories.indices import crear_indices
from gestion_documental.repositories.mapeo import (
    COLECCION_CONTRATISTAS,
    COLECCION_CONTRATOS,
    COLECCION_ROLES,
    COLECCION_USUARIOS,
    COLECCIONES,
    contratista_a_dict,
    contrato_a_dict,
    rol_a_dict,
    usuario_a_dict,
)
from gestion_documental.repositories.mongo import RepositorioCuentasMongo
from gestion_documental.services.servicio_auth import hasher_por_defecto

CONTRASENA_DEMO = "Demo2025*"

PERMISOS = {
    1: "usuarios.gestionar",
    2: "contratistas.gestionar",
    3: "contratistas.consultar",
    4: "contratos.gestionar",
    5: "contratos.consultar",
    6: "cuentas.radicar",
    7: "cuentas.consultar",
    8: "cuentas.editar",
    9: "cuentas.cambiar_estado",
    10: "cuentas.pagar",
    11: "documentos.adjuntar",
    12: "documentos.consultar",
    13: "documentos.eliminar",
}

ROLES = [
    (1, "Administrador", "Administración general del sistema y de usuarios", list(range(1, 14))),
    (2, "Radicador", "Registra cuentas de cobro y adjunta documentos", [3, 5, 6, 7, 8, 11, 12, 13]),
    (3, "Revisor", "Revisa cuentas y cambia su estado", [3, 5, 7, 9, 12]),
    (4, "Supervisor", "Supervisa contratos y cambia el estado de las cuentas", [3, 4, 5, 7, 9, 12]),
    (5, "Consulta", "Solo lectura de cuentas y documentos", [3, 5, 7, 12]),
]

USUARIOS = [
    (1, "Ana", "Rodríguez", "ana.rodriguez@entidad.gov.co", 1,
     "Coordinadora de Gestión Documental", True, "2025-06-20 08:30", 0, None, False,
     "2025-01-06 08:00"),
    (2, "Jorge", "Martínez", "jorge.martinez@entidad.gov.co", 4,
     "Jefe de Presupuesto", True, "2025-06-18 16:45", 0, None, False, "2025-01-06 08:30"),
    (3, "Luz", "Paredes", "luz.paredes@entidad.gov.co", 2,
     "Auxiliar Administrativo", True, "2025-06-25 09:05", 0, None, True, "2025-01-07 09:00"),
    (4, "Ricardo", "Gómez", "ricardo.gomez@entidad.gov.co", 4,
     "Jefe de Servicios Generales", True, "2025-06-19 14:20", 0, None, False, "2025-01-07 09:30"),
    (5, "María", "Cifuentes", "maria.cifuentes@entidad.gov.co", 3,
     "Profesional de Contratación", True, "2025-06-24 15:00", 5, "2025-06-30 10:00", False,
     "2025-01-08 08:00"),
    (6, "Pedro", "Sarmiento", "pedro.sarmiento@entidad.gov.co", 5,
     "Técnico Administrativo", False, None, 0, None, True, "2025-02-03 10:00"),
]  # fmt: skip

CONTRATISTAS: list[tuple[int, type[Contratista], str, str, str, str, str, bool]] = [
    (1, PersonaNatural, "Luis Fernando Rojas", "1024567891", "3112003456",
     "luis.rojas@correo.com", "Calle 12 # 34-56, Bogotá", True),
    (2, PersonaJuridica, "Constructora Andina S.A.S.", "901234567", "6014567890",
     "contacto@constructoraandina.com", "Av. El Dorado # 68A-45, Bogotá", True),
    (3, PersonaNatural, "Carmen Elena Duarte", "52213789", "3125678901",
     "carmen.duarte@correo.com", "Carrera 45 # 78-90, Medellín", True),
    (4, PersonaJuridica, "Servicios Integrales del Caribe Ltda.", "890123456", "6055551234",
     "gerencia@servicioscaribe.com", "Calle 30 # 15-20, Barranquilla", True),
    (5, PersonaNatural, "Andrés Felipe Torres", "76543210", "3156789012",
     "andres.torres@correo.com", "Transversal 5 # 22-11, Cali", True),
    (6, PersonaJuridica, "Almacén y Suministros del Oriente S.A.", "910234567", "6076543210",
     "ventas@suministrosoriente.com", "Cra 23 # 40-55, Bucaramanga", False),
]  # fmt: skip

CONTRATOS = [
    (1, 2, "CONT-2025-001", "Construcción de la sede administrativa del archivo documental.",
     "450000000.00", "2025-01-15", "2025-12-31", EstadoContrato.ACTIVO, 2),
    (2, 1, "CONT-2025-002", "Prestación de servicios de asesoría jurídica en contratación pública.",
     "96000000.00", "2025-02-01", "2025-08-31", EstadoContrato.ACTIVO, 4),
    (3, 3, "CONT-2025-003", "Suministro de papelería y útiles de oficina.",
     "32500000.00", "2025-01-10", "2025-06-30", EstadoContrato.LIQUIDADO, 2),
    (4, 4, "CONT-2025-004", "Servicio de limpieza y mantenimiento de instalaciones.",
     "180000000.00", "2025-03-01", "2026-02-28", EstadoContrato.ACTIVO, 4),
    (5, 5, "CONT-2025-005", "Servicios de soporte técnico en infraestructura de TI.",
     "72000000.00", "2025-04-01", "2025-10-31", EstadoContrato.SUSPENDIDO, 2),
    (6, 1, "CONT-2025-006", "Capacitación en gestión documental para el personal.",
     "18000000.00", "2025-05-01", "2025-07-31", EstadoContrato.TERMINADO, 4),
]  # fmt: skip

CUENTAS = [
    (1, 1, "RAD-2025-0001", "CUENTA-001", "37500000.00",
     "Acta parcial 1 - Construcción sede administrativa.", "2025-03-20",
     "Revisado por presupuesto, sin novedades.", 3),
    (2, 2, "RAD-2025-0002", "CUENTA-001", "8000000.00",
     "Honorarios mes de marzo - asesoría jurídica.", "2025-03-31", None, 3),
    (3, 3, "RAD-2025-0003", "CUENTA-001", "5420000.00",
     "Entrega final suministro de papelería.", "2025-06-25", None, 3),
    (4, 4, "RAD-2025-0004", "CUENTA-001", "15000000.00",
     "Servicio de limpieza del mes de mayo.", "2025-05-31",
     "Falta certificado de paz y salvo del contratista.", 3),
    (5, 5, "RAD-2025-0005", "CUENTA-001", "6000000.00",
     "Soporte técnico abril - mayo.", "2025-06-05", None, 3),
    (6, 6, "RAD-2025-0006", "CUENTA-001", "3000000.00",
     "Primer taller de capacitación en gestión documental.", "2025-06-15",
     "Solicitud anulada por el contratista.", 3),
]  # fmt: skip

E = EstadoCuenta
HISTORIAL = [
    (1, None, E.RECIBIDA, 3, "Cuenta radicada", "2025-03-20 09:00"),
    (1, E.RECIBIDA, E.APROBADA, 5, "Aprobada por contratación", "2025-03-23 09:00"),
    (2, None, E.RECIBIDA, 3, "Cuenta radicada", "2025-03-31 09:00"),
    (2, E.RECIBIDA, E.EN_REVISION, 5, "En revisión de soportes", "2025-04-02 09:00"),
    (3, None, E.RECIBIDA, 3, "Cuenta radicada", "2025-06-25 09:00"),
    (4, None, E.RECIBIDA, 3, "Cuenta radicada", "2025-05-31 09:00"),
    (4, E.RECIBIDA, E.RECHAZADA, 5, "Rechazada: falta paz y salvo", "2025-06-05 09:00"),
    (5, None, E.RECIBIDA, 3, "Cuenta radicada", "2025-06-05 09:00"),
    (5, E.RECIBIDA, E.APROBADA, 5, "Aprobada por contratación", "2025-06-09 09:00"),
    (5, E.APROBADA, E.PAGADA, 1, "Pago efectuado", "2025-06-16 09:00"),
    (6, None, E.RECIBIDA, 3, "Cuenta radicada", "2025-06-15 09:00"),
    (6, E.RECIBIDA, E.ANULADA, 1, "Anulada por solicitud del contratista", "2025-06-17 09:00"),
]

T = TipoDocumento
DOCUMENTOS = [
    (1, T.CUENTA_COBRO, "acta_parcial_1.pdf",
     "aedcbf18f4a5a30426d83622b75e7b1ce5a010b550451fcfcf2dc28fb6789527", 839680),
    (1, T.CERTIFICADO, "certificado_constructora.pdf",
     "b988f59608d692fa62192dcfae2279811f055372fa8fb00f4d5264a72f1ba7d5", 440320),
    (1, T.POLIZA, "poliza_cumplimiento.pdf",
     "42c076369bcd350d9127a5f811263cb6eb8151fec5712853069fd436b54504d4", 655360),
    (2, T.CUENTA_COBRO, "cuenta_cobro_marzo.pdf",
     "46be0955beadf4185e035d9b1fb0b47246a575ba9b917234627af7074879ee82", 399360),
    (3, T.CEDULA, "cedula_luis.jpg", None, None),
    (4, T.RUT, "rut_servicios_caribe.pdf", None, None),
    (5, T.CUENTA_COBRO, "soporte_tecnico_mayo.pdf",
     "6af0cf0895095a5ae12e585681e1b6bb1e9f8b599d84d762b1e07a117863fabf", 286720),
    (6, T.OTRO, "observaciones_anulacion.pdf",
     "dec262043cd5123bed5ddd5cf131c4dd8232077ff13715c522e14971cd97097e", 122880),
]  # fmt: skip


def momento(texto: str) -> datetime:
    return datetime.fromisoformat(texto).replace(tzinfo=UTC)


def momento_opcional(texto: str | None) -> datetime | None:
    return None if texto is None else momento(texto)


def nuevos_ids(cantidad: int) -> dict[int, ObjectId]:
    return {numero: ObjectId() for numero in range(1, cantidad + 1)}


def cargar_roles(db: Database[dict[str, Any]], ids: dict[int, ObjectId]) -> None:
    db[COLECCION_ROLES].insert_many(
        rol_a_dict(
            Rol(
                id=str(ids[id_rol]),
                nombre=nombre,
                descripcion=descripcion,
                permisos=frozenset(PERMISOS[id_permiso] for id_permiso in permisos),
            )
        )
        for id_rol, nombre, descripcion, permisos in ROLES
    )


def cargar_usuarios(
    db: Database[dict[str, Any]], ids: dict[int, ObjectId], ids_roles: dict[int, ObjectId]
) -> None:
    hasher = hasher_por_defecto()
    db[COLECCION_USUARIOS].insert_many(
        usuario_a_dict(
            Usuario(
                id=str(ids[id_usuario]),
                nombre=nombre,
                apellido=apellido,
                correo=correo,
                id_rol=str(ids_roles[id_rol]),
                cargo=cargo,
                contrasena_hash=hasher.hash(CONTRASENA_DEMO),
                activo=activo,
                ultimo_acceso=momento_opcional(ultimo_acceso),
                intentos_fallidos=intentos,
                bloqueado_hasta=momento_opcional(bloqueado_hasta),
                debe_cambiar_contrasena=debe_cambiar,
                fecha_registro=momento(registro),
            )
        )
        for (
            id_usuario,
            nombre,
            apellido,
            correo,
            id_rol,
            cargo,
            activo,
            ultimo_acceso,
            intentos,
            bloqueado_hasta,
            debe_cambiar,
            registro,
        ) in USUARIOS
    )


def imprimir_usuarios_demo() -> None:
    roles = {id_rol: nombre for id_rol, nombre, _, _ in ROLES}
    filas = [
        (correo, roles[id_rol], nota_usuario(activo, intentos, bloqueado_hasta, debe_cambiar))
        for _, _, _, correo, id_rol, _, activo, _, intentos, bloqueado_hasta, debe_cambiar, _ in (
            USUARIOS
        )
    ]
    ancho = max(len(correo) for correo, _, _ in filas)
    print()
    print(f"Usuarios de la demo (contraseña: {CONTRASENA_DEMO})")
    print(f"  {'correo':<{ancho}} | {'rol':<13} | nota")
    print(f"  {'-' * ancho}-+-{'-' * 13}-+-{'-' * 30}")
    for correo, rol, nota in filas:
        print(f"  {correo:<{ancho}} | {rol:<13} | {nota}")


def nota_usuario(
    activo: bool, intentos: int, bloqueado_hasta: str | None, debe_cambiar: bool
) -> str:
    if not activo:
        return "inactivo: no puede entrar"
    notas = []
    if debe_cambiar:
        notas.append("debe cambiar la contraseña")
    if intentos:
        notas.append(f"{intentos} intentos fallidos (bloqueo vencido: {bloqueado_hasta})")
    return "; ".join(notas)


def cargar_contratistas(db: Database[dict[str, Any]], ids: dict[int, ObjectId]) -> None:
    db[COLECCION_CONTRATISTAS].insert_many(
        contratista_a_dict(
            clase(
                id=str(ids[id_contratista]),
                nombre_completo=nombre,
                nit_cedula=nit_cedula,
                telefono=telefono,
                correo=correo,
                direccion=direccion,
                activo=activo,
            )
        )
        for id_contratista, clase, nombre, nit_cedula, telefono, correo, direccion, activo in (
            CONTRATISTAS
        )
    )


def cargar_contratos(
    db: Database[dict[str, Any]],
    ids: dict[int, ObjectId],
    ids_contratistas: dict[int, ObjectId],
    ids_usuarios: dict[int, ObjectId],
) -> None:
    db[COLECCION_CONTRATOS].insert_many(
        contrato_a_dict(
            Contrato(
                id=str(ids[id_contrato]),
                id_contratista=str(ids_contratistas[id_contratista]),
                numero_contrato=numero,
                objeto_contrato=objeto,
                valor_total=ValorMonetario(Decimal(valor)),
                fecha_inicio=date.fromisoformat(inicio),
                fecha_fin=date.fromisoformat(fin),
                estado=estado,
                id_supervisor=str(ids_usuarios[supervisor]),
            )
        )
        for id_contrato, id_contratista, numero, objeto, valor, inicio, fin, estado, supervisor in (
            CONTRATOS
        )
    )


def documentos_de(id_cuenta: int, id_usuario: str, fecha: datetime) -> list[Documento]:
    documentos: list[Documento] = []
    for cuenta, tipo, nombre, hash_sha256, tamano in DOCUMENTOS:
        if cuenta != id_cuenta:
            continue
        if hash_sha256 is None:
            documentos.append(
                DocumentoURL(
                    nombre_original=nombre,
                    ruta_archivo=f"https://example.com/{nombre}",
                    tipo=tipo,
                    id_usuario=id_usuario,
                    fecha_carga=fecha,
                )
            )
        else:
            documentos.append(
                DocumentoPDF(
                    nombre_original=nombre,
                    ruta_archivo=f"/uploads/{nombre}",
                    tipo=tipo,
                    id_usuario=id_usuario,
                    fecha_carga=fecha,
                    tipo_mime="application/pdf",
                    hash_sha256=hash_sha256,
                    tamano_bytes=tamano,
                )
            )
    return documentos


def cargar_cuentas(
    db: Database[dict[str, Any]],
    ids_contratos: dict[int, ObjectId],
    ids_usuarios: dict[int, ObjectId],
) -> None:
    repositorio = RepositorioCuentasMongo(db)
    for (
        id_cuenta,
        id_contrato,
        radicado,
        numero,
        valor,
        concepto,
        fecha,
        observ,
        id_usuario,
    ) in CUENTAS:
        radicador = str(ids_usuarios[id_usuario])
        historial = [
            CambioEstado(
                estado_anterior=anterior,
                estado_nuevo=nuevo,
                id_usuario=str(ids_usuarios[usuario]),
                observacion=observacion,
                fecha_cambio=momento(cuando),
            )
            for cuenta, anterior, nuevo, usuario, observacion, cuando in HISTORIAL
            if cuenta == id_cuenta
        ]
        repositorio.guardar(
            CuentaCobro(
                numero_radicado=radicado,
                numero_cuenta=numero,
                id_contrato=str(ids_contratos[id_contrato]),
                valor_cobro=ValorMonetario(Decimal(valor)),
                concepto_pago=concepto,
                fecha_presentacion=date.fromisoformat(fecha),
                id_usuario=radicador,
                observaciones=observ,
                documentos=documentos_de(id_cuenta, radicador, historial[0].fecha_cambio),
                historial=historial,
            )
        )


def main() -> None:
    db = get_db()
    for coleccion in COLECCIONES:
        db.drop_collection(coleccion)
    crear_indices(db)

    ids_roles = nuevos_ids(len(ROLES))
    ids_usuarios = nuevos_ids(len(USUARIOS))
    ids_contratistas = nuevos_ids(len(CONTRATISTAS))
    ids_contratos = nuevos_ids(len(CONTRATOS))

    cargar_roles(db, ids_roles)
    cargar_usuarios(db, ids_usuarios, ids_roles)
    cargar_contratistas(db, ids_contratistas)
    cargar_contratos(db, ids_contratos, ids_contratistas, ids_usuarios)
    cargar_cuentas(db, ids_contratos, ids_usuarios)

    print(f"Base de datos: {db.name}")
    for coleccion in COLECCIONES:
        print(f"  {coleccion}: {db[coleccion].count_documents({})}")
    imprimir_usuarios_demo()


if __name__ == "__main__":
    main()
