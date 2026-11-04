import inspect
from datetime import date
from decimal import Decimal

import pytest

from gestion_documental.datos_sinteticos import pdf_sintetico
from gestion_documental.domain.documentos import DocumentoLocal, DocumentoPDF
from gestion_documental.domain.enums import EstadoContrato, EstadoCuenta, TipoDocumento, TipoPersona
from gestion_documental.domain.errores import ArchivoInvalidoError, ErrorDominio, NoEncontradoError
from gestion_documental.events import suscriptores
from gestion_documental.events.auditoria import FiltroAuditoria
from gestion_documental.events.comandos import (
    AdjuntarArchivo,
    CambiarEstadoCuenta,
    EditarCuenta,
    RadicarCuenta,
)
from gestion_documental.events.eventos import (
    ContratoCambiado,
    CuentaAnulada,
    CuentaEditada,
    CuentaPagada,
    DocumentoEliminado,
    EstadoCuentaCambiado,
    EventoDominio,
)
from gestion_documental.events.publicador import BusEventosEnMemoria
from gestion_documental.events.suscriptores import NotificadorSupervisor, RegistroAuditoria
from gestion_documental.repositories.base import RegistroDuplicadoError
from gestion_documental.repositories.memoria import RepositorioArchivosEnMemoria
from gestion_documental.services.servicio_cuentas import IntegridadArchivoError
from tests.fabricas import Escenario, escenario, radicar

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
SUPERVISOR = "supervisor@example.com"
RADICADOR = "radicador@example.com"


def radicar_con(esc: Escenario, **cambios: object) -> str:
    comando = radicar().model_copy(update=cambios)
    return esc.cuentas().radicar(comando).numero_radicado


def subir(esc: Escenario, contenido: bytes, radicado: str = "RAD-SINT-0001") -> DocumentoLocal:
    documento = esc.cuentas().adjuntar_archivo(
        AdjuntarArchivo(
            id_usuario="u1",
            numero_radicado=radicado,
            nombre_original="soporte",
            tipo=TipoDocumento.CERTIFICADO,
        ),
        contenido,
    )
    assert isinstance(documento, DocumentoLocal)
    return documento


def test_radicar_exige_contrato_activo_y_vigente() -> None:
    esc = escenario()

    with pytest.raises(ErrorDominio, match="fuera de la vigencia"):
        radicar_con(esc, fecha_presentacion=date(2025, 12, 31))
    esc.contratos().cambiar_estado("CONT-SINT-001", EstadoContrato.SUSPENDIDO, "u1")
    with pytest.raises(ErrorDominio, match="SUSPENDIDO"):
        radicar_con(esc)


def test_tope_del_contrato_excluye_anuladas_y_rechazadas() -> None:
    esc = escenario()
    servicio = esc.cuentas()
    radicar_con(esc, valor_cobro=Decimal("9000000.00"))

    with pytest.raises(ErrorDominio, match="saldo del contrato"):
        radicar_con(
            esc, numero_radicado="RAD-2", numero_cuenta="C-2", valor_cobro=Decimal("1000000.01")
        )
    servicio.anular("RAD-SINT-0001", "u1", "Error de digitación")
    radicar_con(
        esc, numero_radicado="RAD-2", numero_cuenta="C-2", valor_cobro=Decimal("10000000.00")
    )


def test_editar_valida_estado_tope_y_publica() -> None:
    esc = escenario()
    servicio = esc.cuentas()
    radicar_con(esc)

    servicio.editar(
        EditarCuenta(id_usuario="u1", numero_radicado="RAD-SINT-0001", concepto_pago="Nuevo")
    )
    with pytest.raises(ErrorDominio, match="saldo"):
        servicio.editar(
            EditarCuenta(
                id_usuario="u1", numero_radicado="RAD-SINT-0001", valor_cobro=Decimal("10000000.01")
            )
        )
    servicio.anular("RAD-SINT-0001", "u1", None)
    with pytest.raises(ErrorDominio, match="solo se modifica"):
        servicio.editar(
            EditarCuenta(id_usuario="u1", numero_radicado="RAD-SINT-0001", concepto_pago="Otro")
        )

    editadas = [e for e in esc.recolector.eventos if isinstance(e, CuentaEditada)]
    assert [e.campos for e in editadas] == [("concepto_pago",)]


def test_pagar_y_anular_publican_subclases_de_estado_cambiado() -> None:
    esc = escenario()
    servicio = esc.cuentas()
    radicar_con(esc)
    radicar_con(esc, numero_radicado="RAD-2", numero_cuenta="C-2")
    for estado in (EstadoCuenta.EN_REVISION, EstadoCuenta.APROBADA):
        servicio.cambiar_estado(
            CambiarEstadoCuenta(
                id_usuario="u1", numero_radicado="RAD-SINT-0001", nuevo_estado=estado
            )
        )

    servicio.pagar("RAD-SINT-0001", "u1", "Transferencia")
    servicio.anular("RAD-2", "u1", None)

    pagada, anulada = esc.recolector.eventos[-2:]
    assert isinstance(pagada, CuentaPagada)
    assert isinstance(anulada, CuentaAnulada)
    assert isinstance(pagada, EstadoCuentaCambiado)


def test_auditoria_recibe_eventos_nuevos_sin_cambiar_su_codigo() -> None:
    bus = BusEventosEnMemoria()
    auditoria = RegistroAuditoria()
    bus.suscribir(EventoDominio, auditoria)
    nuevos: list[EventoDominio] = [
        CuentaPagada(
            id_usuario="u",
            numero_radicado="R",
            estado_anterior=EstadoCuenta.APROBADA,
            estado_nuevo=EstadoCuenta.PAGADA,
        ),
        CuentaAnulada(
            id_usuario="u",
            numero_radicado="R",
            estado_anterior=EstadoCuenta.RECIBIDA,
            estado_nuevo=EstadoCuenta.ANULADA,
        ),
        CuentaEditada(id_usuario="u", numero_radicado="R", campos=("valor_cobro",)),
        DocumentoEliminado(
            id_usuario="u", numero_radicado="R", id_documento="d", nombre_original="a.pdf"
        ),
        ContratoCambiado(
            id_usuario="u",
            numero_contrato="C",
            estado_anterior=EstadoContrato.ACTIVO,
            estado_nuevo=EstadoContrato.SUSPENDIDO,
        ),
    ]

    for evento in nuevos:
        bus.publicar(evento)

    codigo = inspect.getsource(RegistroAuditoria)
    assert not any(type(evento).__name__ in codigo for evento in nuevos)
    assert [linea.split("] ")[0].split("[")[1] for linea in auditoria.lineas] == [
        type(evento).__name__ for evento in nuevos
    ]
    assert inspect.getsourcefile(RegistroAuditoria) == inspect.getsourcefile(suscriptores)


def test_notificador_recibe_pagada_por_herencia_pero_no_la_notifica() -> None:
    bus = BusEventosEnMemoria()
    notificador = NotificadorSupervisor()
    bus.suscribir(EstadoCuentaCambiado, notificador)

    bus.publicar(
        CuentaPagada(
            id_usuario="u",
            numero_radicado="R",
            estado_anterior=EstadoCuenta.APROBADA,
            estado_nuevo=EstadoCuenta.PAGADA,
        )
    )

    assert notificador.mensajes == ()


def test_auditoria_persistente_filtra_por_tipo() -> None:
    esc = escenario()
    radicar_con(esc)
    esc.cuentas().anular("RAD-SINT-0001", "u1", None)

    anuladas = esc.repos.auditoria.buscar(FiltroAuditoria(tipo="CuentaAnulada"))
    todos = esc.repos.auditoria.buscar(FiltroAuditoria())

    assert [r.tipo for r in anuladas] == ["CuentaAnulada"]
    assert {r.tipo for r in todos} == {"CuentaRadicada", "CuentaAnulada"}
    assert anuladas[0].datos["numero_radicado"] == "RAD-SINT-0001"


def test_subir_pdf_crea_documento_pdf_con_hash_real() -> None:
    esc = escenario()
    radicar_con(esc)
    contenido = pdf_sintetico("Soporte sintético")

    documento = subir(esc, contenido)

    assert isinstance(documento, DocumentoPDF)
    assert documento.tamano_bytes == len(contenido)
    assert documento.verificar_hash(contenido)
    assert isinstance(esc.repos.archivos, RepositorioArchivosEnMemoria)
    assert esc.repos.archivos.existe(documento.ruta_archivo)


def test_subir_png_crea_documento_local() -> None:
    esc = escenario()
    radicar_con(esc)

    documento = subir(esc, PNG)

    assert type(documento) is DocumentoLocal
    assert documento.tipo_mime == "image/png"


def test_subir_archivo_no_permitido_no_guarda_nada() -> None:
    esc = escenario()
    radicar_con(esc)

    with pytest.raises(ArchivoInvalidoError):
        subir(esc, b"<script>alert(1)</script>")

    assert esc.cuentas().obtener("RAD-SINT-0001").documentos == ()


def test_si_falla_guardar_la_cuenta_se_borra_el_archivo() -> None:
    esc = escenario()
    radicar_con(esc)
    esc.cuentas().anular("RAD-SINT-0001", "u1", None)
    archivos = esc.repos.archivos
    assert isinstance(archivos, RepositorioArchivosEnMemoria)

    with pytest.raises(ErrorDominio, match="ANULADA"):
        subir(esc, PNG)

    assert archivos._archivos == {}


def test_descarga_verifica_el_hash() -> None:
    esc = escenario()
    radicar_con(esc)
    contenido = pdf_sintetico("Original")
    documento = subir(esc, contenido)

    _, bloques = esc.cuentas().descargar("RAD-SINT-0001", documento.id_documento)
    assert b"".join(bloques) == contenido

    archivos = esc.repos.archivos
    assert isinstance(archivos, RepositorioArchivosEnMemoria)
    archivos.reemplazar(documento.ruta_archivo, pdf_sintetico("Alterado"))
    with pytest.raises(IntegridadArchivoError):
        esc.cuentas().descargar("RAD-SINT-0001", documento.id_documento)


def test_eliminar_documento_borra_el_archivo_y_publica() -> None:
    esc = escenario()
    radicar_con(esc)
    documento = subir(esc, PNG)

    esc.cuentas().eliminar_documento("RAD-SINT-0001", documento.id_documento, "u1")

    archivos = esc.repos.archivos
    assert isinstance(archivos, RepositorioArchivosEnMemoria)
    assert not archivos.existe(documento.ruta_archivo)
    assert isinstance(esc.recolector.eventos[-1], DocumentoEliminado)
    with pytest.raises(NoEncontradoError):
        esc.cuentas().descargar("RAD-SINT-0001", documento.id_documento)


def test_buscar_con_filtros_y_paginacion() -> None:
    esc = escenario()
    for indice in range(1, 6):
        radicar_con(
            esc,
            numero_radicado=f"RAD-{indice}",
            numero_cuenta=f"C-{indice}",
            valor_cobro=Decimal("100.00"),
            fecha_presentacion=date(2026, indice, 1),
        )
    servicio = esc.cuentas()

    pagina = servicio.buscar(pagina=2, tamano=2)
    por_fecha = servicio.buscar(desde=date(2026, 2, 1), hasta=date(2026, 3, 31))
    por_contratista = servicio.buscar(nit_contratista="900000001-2", tamano=1)
    sin_contratos = servicio.buscar(nit_contratista="1000000001")

    assert (pagina.total, [c.numero_radicado for c in pagina.items]) == (5, ["RAD-3", "RAD-4"])
    assert [c.numero_radicado for c in por_fecha.items] == ["RAD-2", "RAD-3"]
    assert por_contratista.total == 5
    assert sin_contratos.total == 0


def test_resumen_por_estado_y_contrato() -> None:
    esc = escenario()
    radicar_con(esc, valor_cobro=Decimal("100.00"))
    radicar_con(esc, numero_radicado="RAD-2", numero_cuenta="C-2", valor_cobro=Decimal("50.50"))
    esc.cuentas().anular("RAD-2", "u1", None)

    resumen = esc.cuentas().resumen()

    assert [(g.clave, g.cantidad, g.total) for g in resumen.por_estado] == [
        ("ANULADA", 1, Decimal("50.50")),
        ("RECIBIDA", 1, Decimal("100.00")),
    ]
    assert [(g.clave, g.cantidad) for g in resumen.por_contrato] == [("CONT-SINT-001", 2)]


def test_contrato_exige_supervisor_activo_con_rol_supervisor() -> None:
    esc = escenario()
    servicio = esc.contratos()
    datos = {
        "numero_contrato": "CONT-NUEVO",
        "nit_contratista": "900000001-2",
        "objeto_contrato": "Objeto",
        "valor_total": Decimal("1000.00"),
        "fecha_inicio": date(2026, 1, 1),
        "fecha_fin": date(2026, 12, 31),
    }

    with pytest.raises(ErrorDominio, match="rol Supervisor"):
        servicio.crear(**datos, id_supervisor=esc.id_de(RADICADOR))  # type: ignore[arg-type]
    supervisor = esc.usuario(SUPERVISOR)
    supervisor.desactivar()
    esc.repos.usuarios.guardar(supervisor)
    with pytest.raises(ErrorDominio, match="inactivo"):
        servicio.crear(**datos, id_supervisor=esc.id_de(SUPERVISOR))  # type: ignore[arg-type]


def test_no_se_crean_contratos_para_contratistas_inactivos() -> None:
    esc = escenario()

    with pytest.raises(ErrorDominio, match="inactivo"):
        esc.contratos().crear(
            numero_contrato="CONT-X",
            nit_contratista="1000000001",
            objeto_contrato="Objeto",
            valor_total=Decimal("1000.00"),
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
            id_supervisor=esc.id_de(SUPERVISOR),
        )


def test_cambio_de_estado_de_contrato_publica_evento() -> None:
    esc = escenario()

    esc.contratos().cambiar_estado("CONT-SINT-001", EstadoContrato.SUSPENDIDO, "u1")

    evento = esc.recolector.eventos[-1]
    assert isinstance(evento, ContratoCambiado)
    assert evento.estado_nuevo is EstadoContrato.SUSPENDIDO


def test_valor_total_no_baja_de_lo_comprometido() -> None:
    esc = escenario()
    radicar_con(esc, valor_cobro=Decimal("5000.00"))

    with pytest.raises(ErrorDominio, match="menor que lo ya cobrado"):
        esc.contratos().editar("CONT-SINT-001", valor_total=Decimal("4999.99"))


def test_crear_usuario_con_contrasena_temporal() -> None:
    esc = escenario()

    usuario, temporal = esc.usuarios().crear(
        nombre="Nuevo",
        apellido="Sintético",
        correo="Nuevo2@Example.com",
        cargo="Aux",
        rol="Consulta",
    )

    assert usuario.correo == "nuevo2@example.com"
    assert usuario.debe_cambiar_contrasena
    assert len(temporal) >= 12
    with pytest.raises(RegistroDuplicadoError):
        esc.usuarios().crear(
            nombre="Otro", apellido="X", correo="nuevo2@example.com", cargo="Aux", rol="Consulta"
        )


def test_gestion_de_usuarios() -> None:
    esc = escenario()
    servicio = esc.usuarios()
    id_radicador = esc.id_de(RADICADOR)

    servicio.cambiar_rol(id_radicador, "Revisor")
    servicio.desactivar(id_radicador, esc.id_de("administrador@example.com"))
    usuario = esc.usuario(RADICADOR)
    usuario.intentos_fallidos = 5
    esc.repos.usuarios.guardar(usuario)
    servicio.reiniciar_bloqueo(id_radicador)

    final = esc.usuario(RADICADOR)
    assert servicio.rol(final.id_rol).nombre == "Revisor"
    assert not final.activo
    assert final.intentos_fallidos == 0
    with pytest.raises(ErrorDominio, match="sí mismo"):
        servicio.desactivar(id_radicador, id_radicador)
    with pytest.raises(NoEncontradoError):
        servicio.cambiar_rol(id_radicador, "Inventado")


def test_contratistas_crear_buscar_y_desactivar() -> None:
    esc = escenario()
    servicio = esc.contratistas()

    nuevo = servicio.crear(
        tipo_persona=TipoPersona.NATURAL,
        nombre_completo="Ana Sintética",
        nit_cedula="52000001",
        telefono=None,
        correo=None,
        direccion=None,
        id_usuario="u1",
    )
    assert nuevo.id is not None
    servicio.desactivar(nuevo.id, "u2")

    assert [c.nombre_completo for c in servicio.buscar("sintética")] == [
        "Ana Sintética",
        "Empresa Sintética S.A.S.",
        "Persona Sintética Inactiva",
    ]
    assert [c.nit_cedula for c in servicio.buscar("9000")] == ["900000001-2"]
    assert [c.nombre_completo for c in servicio.buscar(solo_activos=True)] == [
        "Empresa Sintética S.A.S."
    ]
    desactivado = servicio.obtener(nuevo.id)
    assert (desactivado.activo, desactivado.modificado_por) == (False, "u2")
    with pytest.raises(RegistroDuplicadoError):
        servicio.crear(
            tipo_persona=TipoPersona.NATURAL,
            nombre_completo="Duplicado",
            nit_cedula="52000001",
            telefono=None,
            correo=None,
            direccion=None,
            id_usuario="u1",
        )


def test_radicar_sigue_publicando_cuenta_radicada() -> None:
    esc = escenario()

    esc.cuentas().radicar(RadicarCuenta.model_validate(radicar().model_dump()))

    assert type(esc.recolector.eventos[0]).__name__ == "CuentaRadicada"
