import argparse
import hashlib
from datetime import date
from decimal import Decimal
from typing import Any

from bson import ObjectId

from gestion_documental.datos_sinteticos import pdf_sintetico
from gestion_documental.domain.contratistas import PersonaJuridica
from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.documentos import (
    Documento,
    DocumentoLocal,
    DocumentoPDF,
    DocumentoURL,
)
from gestion_documental.domain.enums import EstadoCuenta, TipoDocumento
from gestion_documental.domain.errores import TransicionInvalidaError
from gestion_documental.domain.tiempo import ahora_utc
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.events.comandos import AdjuntarArchivo, CambiarEstadoCuenta, RadicarCuenta
from gestion_documental.events.eventos import EstadoCuentaCambiado, EventoDominio
from gestion_documental.events.publicador import BusEventosEnMemoria, EventSubscriber
from gestion_documental.events.suscriptores import NotificadorSupervisor, RegistroAuditoria
from gestion_documental.repositories.base import Repositorios
from gestion_documental.repositories.memoria import repositorios_en_memoria
from gestion_documental.services.servicio_cuentas import ServicioCuentas

CONTENIDO = b"contenido sintetico de la demo"


class ContadorPato:
    def __init__(self) -> None:
        self.recibidos = 0

    def manejar(self, evento: EventoDominio) -> None:
        self.recibidos += 1


def seccion(titulo: str) -> None:
    print(f"\n=== {titulo} ===")


def documentos_mixtos(id_usuario: str) -> list[Documento]:
    comunes: dict[str, Any] = {"id_usuario": id_usuario}
    return [
        DocumentoPDF(
            **comunes,
            nombre_original="cuenta_demo.pdf",
            ruta_archivo="/uploads/cuenta_demo.pdf",
            tipo=TipoDocumento.CUENTA_COBRO,
            tipo_mime="application/pdf",
            hash_sha256=hashlib.sha256(CONTENIDO).hexdigest(),
            tamano_bytes=len(CONTENIDO),
        ),
        DocumentoLocal(
            **comunes,
            nombre_original="certificado_demo.png",
            ruta_archivo="/uploads/certificado_demo.png",
            tipo=TipoDocumento.CERTIFICADO,
            tipo_mime="image/png",
            hash_sha256=hashlib.sha256(b"png").hexdigest(),
            tamano_bytes=3,
        ),
        DocumentoURL(
            **comunes,
            nombre_original="rut_demo.pdf",
            ruta_archivo="https://example.com/rut_demo.pdf",
            tipo=TipoDocumento.RUT,
        ),
    ]


def preparar_memoria() -> tuple[Repositorios, str, str]:
    contrato = Contrato(
        id=str(ObjectId()),
        numero_contrato="CONT-DEMO-001",
        id_contratista=str(ObjectId()),
        objeto_contrato="Contrato sintético de la demo",
        valor_total=ValorMonetario(Decimal("50000000.00")),
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 12, 31),
        id_supervisor=str(ObjectId()),
    )
    return repositorios_en_memoria(contratos=[contrato]), contrato.numero_contrato, str(ObjectId())


def preparar_mongo() -> tuple[Repositorios, str, str]:
    from gestion_documental.repositories.conexion import get_db
    from gestion_documental.repositories.mongo import repositorios_mongo

    db = get_db()
    radicador = db["usuarios"].find_one({"correo": "luz.paredes@entidad.gov.co"})
    if radicador is None:
        raise SystemExit("La base está vacía: ejecuta antes uv run python scripts/seed.py")
    return repositorios_mongo(db), "CONT-2025-001", str(radicador["_id"])


def demo_abstraccion() -> None:
    seccion("1. Abstracción: Documento es abstracto")
    try:
        Documento(  # type: ignore[abstract]
            nombre_original="x.pdf",
            ruta_archivo="/x.pdf",
            tipo=TipoDocumento.OTRO,
            id_usuario="u",
        )
    except TypeError as error:
        print(f"TypeError: {error}")


def demo_herencia() -> None:
    seccion("2. Herencia y MRO")
    for clase in (DocumentoPDF, PersonaJuridica):
        print(f"{clase.__name__}: {' -> '.join(c.__name__ for c in clase.__mro__)}")


def demo_lsp(id_usuario: str) -> None:
    seccion("3. LSP: documentos mixtos tratados como Documento")
    for documento in documentos_mixtos(id_usuario):
        documento.validar()
        print(f"{type(documento).__name__:15} {documento.describir()}")


def demo_flujo(
    repos: Repositorios, numero_contrato: str, usuario: str
) -> tuple[ServicioCuentas, str, ContadorPato]:
    seccion("4. Flujo completo: radicar -> adjuntar PDF -> revisar -> aprobar")
    bus = BusEventosEnMemoria()
    auditoria = RegistroAuditoria()
    notificador = NotificadorSupervisor()
    pato = ContadorPato()
    bus.suscribir(EventoDominio, auditoria)
    bus.suscribir(EstadoCuentaCambiado, notificador)
    bus.suscribir(EventoDominio, pato)
    servicio = ServicioCuentas(
        repos.cuentas, repos.contratos, repos.contratistas, repos.archivos, bus
    )
    contrato = repos.contratos.obtener_por_numero(numero_contrato)
    assert contrato is not None

    sufijo = ahora_utc().strftime("%Y%m%d%H%M%S")
    radicado = f"RAD-DEMO-{sufijo}"
    servicio.radicar(
        RadicarCuenta(
            id_usuario=usuario,
            numero_radicado=radicado,
            numero_cuenta=f"CUENTA-DEMO-{sufijo}",
            numero_contrato=numero_contrato,
            valor_cobro=Decimal("2500000.00"),
            concepto_pago="Cuenta sintética de la demo",
            fecha_presentacion=contrato.fecha_inicio,
        )
    )
    documento = servicio.adjuntar_archivo(
        AdjuntarArchivo(
            id_usuario=usuario,
            numero_radicado=radicado,
            nombre_original="cuenta_demo.pdf",
            tipo=TipoDocumento.CUENTA_COBRO,
        ),
        pdf_sintetico("Cuenta de cobro sintética", radicado),
    )
    print(f"Adjunto guardado como {type(documento).__name__} en {type(repos.archivos).__name__}")
    for estado in (EstadoCuenta.EN_REVISION, EstadoCuenta.APROBADA):
        servicio.cambiar_estado(
            CambiarEstadoCuenta(id_usuario=usuario, numero_radicado=radicado, nuevo_estado=estado)
        )

    print("Auditoría (suscrita a EventoDominio):")
    for linea in auditoria.lineas:
        print(f"  {linea}")
    print("Notificador (suscrito solo a EstadoCuentaCambiado):")
    for mensaje in notificador.mensajes:
        print(f"  {mensaje}")
    return servicio, radicado, pato


def demo_duck_typing(pato: ContadorPato) -> None:
    seccion("5. Duck typing: ContadorPato no hereda de EventSubscriber")
    print(f"isinstance(pato, EventSubscriber) = {isinstance(pato, EventSubscriber)}")
    print(f"Eventos recibidos por el pato: {pato.recibidos}")


def demo_transicion_invalida(servicio: ServicioCuentas, radicado: str, usuario: str) -> None:
    seccion("6. Transición inválida rechazada")
    try:
        servicio.cambiar_estado(
            CambiarEstadoCuenta(
                id_usuario=usuario, numero_radicado=radicado, nuevo_estado=EstadoCuenta.RECIBIDA
            )
        )
    except TransicionInvalidaError as error:
        print(f"TransicionInvalidaError: {error}")
    print(f"Estado guardado: {servicio.obtener(radicado).estado}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Demostración del proyecto de gestión documental")
    parser.add_argument("--mongo", action="store_true", help="usar MongoDB Atlas (.env)")
    argumentos = parser.parse_args()

    repos, contrato, usuario = preparar_mongo() if argumentos.mongo else preparar_memoria()
    print(f"Persistencia: {type(repos.cuentas).__name__}")

    demo_abstraccion()
    demo_herencia()
    demo_lsp(usuario)
    servicio, radicado, pato = demo_flujo(repos, contrato, usuario)
    demo_duck_typing(pato)
    demo_transicion_invalida(servicio, radicado, usuario)


if __name__ == "__main__":
    main()
