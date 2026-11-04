from decimal import Decimal

import pytest

from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.documentos import DocumentoPDF, DocumentoURL
from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento, TipoDocumento
from gestion_documental.domain.errores import ErrorDominio, TransicionInvalidaError
from gestion_documental.events.comandos import AdjuntarDocumento, CambiarEstadoCuenta
from gestion_documental.events.eventos import (
    CuentaRadicada,
    DocumentoAdjuntado,
    EstadoCuentaCambiado,
)
from gestion_documental.repositories.base import RegistroDuplicadoError
from gestion_documental.repositories.memoria import RepositorioCuentasEnMemoria
from gestion_documental.services.servicio_cuentas import NoEncontradoError
from tests.fabricas import CONTRATO_ID, USUARIO_ID, radicar, servicio_en_memoria


def cambiar(estado: EstadoCuenta, radicado: str = "RAD-SINT-0001") -> CambiarEstadoCuenta:
    return CambiarEstadoCuenta(id_usuario=USUARIO_ID, numero_radicado=radicado, nuevo_estado=estado)


def adjuntar(**cambios: object) -> AdjuntarDocumento:
    datos: dict[str, object] = {
        "id_usuario": USUARIO_ID,
        "numero_radicado": "RAD-SINT-0001",
        "nombre_original": "cuenta.pdf",
        "ruta_archivo": "/uploads/cuenta.pdf",
        "tipo": TipoDocumento.CUENTA_COBRO,
        "origen": OrigenDocumento.LOCAL,
        "tipo_mime": "application/pdf",
        "hash_sha256": "a" * 64,
        "tamano_bytes": 2048,
        **cambios,
    }
    return AdjuntarDocumento.model_validate(datos)


class RepositorioQueFallaAlGuardar(RepositorioCuentasEnMemoria):
    def guardar(self, cuenta: CuentaCobro) -> None:
        raise RuntimeError("fallo sintético de la base de datos")


def test_radicar_guarda_y_publica_cuenta_radicada() -> None:
    servicio, cuentas, recolector = servicio_en_memoria()

    cuenta = servicio.radicar(radicar())

    assert cuenta.id_contrato == CONTRATO_ID
    assert cuentas.obtener_por_radicado("RAD-SINT-0001") is not None
    assert len(recolector.eventos) == 1
    evento = recolector.eventos[0]
    assert isinstance(evento, CuentaRadicada)
    assert evento.valor_cobro == Decimal("1500000.00")


def test_radicar_con_contrato_inexistente() -> None:
    servicio, _, recolector = servicio_en_memoria()
    comando = radicar().model_copy(update={"numero_contrato": "CONT-NO-EXISTE"})

    with pytest.raises(NoEncontradoError, match="CONT-NO-EXISTE"):
        servicio.radicar(comando)

    assert recolector.eventos == []


def test_radicado_duplicado() -> None:
    servicio, _, recolector = servicio_en_memoria()
    servicio.radicar(radicar())
    comando = radicar().model_copy(update={"numero_cuenta": "CUENTA-002"})

    with pytest.raises(RegistroDuplicadoError, match="radicado"):
        servicio.radicar(comando)

    assert len(recolector.eventos) == 1


def test_numero_cuenta_duplicado_en_el_contrato() -> None:
    servicio, _, _ = servicio_en_memoria()
    servicio.radicar(radicar())
    comando = radicar().model_copy(update={"numero_radicado": "RAD-SINT-0002"})

    with pytest.raises(RegistroDuplicadoError, match="CUENTA-001"):
        servicio.radicar(comando)


def test_cambio_valido_guarda_y_publica() -> None:
    servicio, cuentas, recolector = servicio_en_memoria()
    servicio.radicar(radicar())

    servicio.cambiar_estado(cambiar(EstadoCuenta.EN_REVISION))

    guardada = cuentas.obtener_por_radicado("RAD-SINT-0001")
    assert guardada is not None
    assert guardada.estado is EstadoCuenta.EN_REVISION
    evento = recolector.eventos[-1]
    assert isinstance(evento, EstadoCuentaCambiado)
    assert (evento.estado_anterior, evento.estado_nuevo) == (
        EstadoCuenta.RECIBIDA,
        EstadoCuenta.EN_REVISION,
    )


def test_transicion_invalida_no_guarda_ni_publica() -> None:
    servicio, cuentas, recolector = servicio_en_memoria()
    servicio.radicar(radicar())

    with pytest.raises(TransicionInvalidaError):
        servicio.cambiar_estado(cambiar(EstadoCuenta.PAGADA))

    guardada = cuentas.obtener_por_radicado("RAD-SINT-0001")
    assert guardada is not None
    assert guardada.estado is EstadoCuenta.RECIBIDA
    assert len(guardada.historial) == 1
    assert len(recolector.eventos) == 1


def test_cambiar_estado_de_cuenta_inexistente() -> None:
    servicio, _, _ = servicio_en_memoria()

    with pytest.raises(NoEncontradoError):
        servicio.cambiar_estado(cambiar(EstadoCuenta.EN_REVISION, "RAD-NO-EXISTE"))


def test_no_publica_si_guardar_falla() -> None:
    servicio, _, recolector = servicio_en_memoria(RepositorioQueFallaAlGuardar())

    with pytest.raises(RuntimeError):
        servicio.radicar(radicar())

    assert recolector.eventos == []


def test_adjuntar_construye_el_documento_correcto_y_publica() -> None:
    servicio, _, recolector = servicio_en_memoria()
    servicio.radicar(radicar())

    servicio.adjuntar(adjuntar())
    cuenta = servicio.adjuntar(
        adjuntar(
            nombre_original="rut.pdf",
            ruta_archivo="https://example.com/rut.pdf",
            tipo=TipoDocumento.RUT,
            origen=OrigenDocumento.URL,
            tipo_mime=None,
            hash_sha256=None,
            tamano_bytes=None,
        )
    )

    assert [type(d) for d in cuenta.documentos] == [DocumentoPDF, DocumentoURL]
    assert [type(e) for e in recolector.eventos[1:]] == [DocumentoAdjuntado, DocumentoAdjuntado]


def test_adjuntar_local_incompleto_no_guarda_ni_publica() -> None:
    servicio, cuentas, recolector = servicio_en_memoria()
    servicio.radicar(radicar())

    with pytest.raises(ErrorDominio, match="exige tipo_mime"):
        servicio.adjuntar(adjuntar(hash_sha256=None))

    guardada = cuentas.obtener_por_radicado("RAD-SINT-0001")
    assert guardada is not None
    assert guardada.documentos == ()
    assert len(recolector.eventos) == 1
