from gestion_documental.domain.cuenta_cobro import CuentaCobro
from gestion_documental.domain.documentos import (
    MIME_PDF,
    Documento,
    DocumentoLocal,
    DocumentoPDF,
    DocumentoURL,
)
from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.events.comandos import AdjuntarDocumento, CambiarEstadoCuenta, RadicarCuenta
from gestion_documental.events.eventos import (
    CuentaRadicada,
    DocumentoAdjuntado,
    EstadoCuentaCambiado,
)
from gestion_documental.events.publicador import EventPublisher
from gestion_documental.repositories.base import (
    RegistroDuplicadoError,
    RepositorioContratos,
    RepositorioCuentas,
)


class NoEncontradoError(Exception):
    pass


def construir_documento(comando: AdjuntarDocumento) -> Documento:
    if comando.origen is OrigenDocumento.URL:
        return DocumentoURL(
            nombre_original=comando.nombre_original,
            ruta_archivo=comando.ruta_archivo,
            tipo=comando.tipo,
            id_usuario=comando.id_usuario,
        )
    clase = DocumentoPDF if comando.tipo_mime == MIME_PDF else DocumentoLocal
    return clase(
        nombre_original=comando.nombre_original,
        ruta_archivo=comando.ruta_archivo,
        tipo=comando.tipo,
        id_usuario=comando.id_usuario,
        tipo_mime=comando.tipo_mime,
        hash_sha256=comando.hash_sha256,
        tamano_bytes=comando.tamano_bytes,
    )


class ServicioCuentas:
    def __init__(
        self,
        cuentas: RepositorioCuentas,
        contratos: RepositorioContratos,
        publicador: EventPublisher,
    ) -> None:
        self._cuentas = cuentas
        self._contratos = contratos
        self._publicador = publicador

    def obtener(self, numero_radicado: str) -> CuentaCobro:
        cuenta = self._cuentas.obtener_por_radicado(numero_radicado)
        if cuenta is None:
            raise NoEncontradoError(f"No existe la cuenta con radicado {numero_radicado}")
        return cuenta

    def listar_por_estado(self, estado: EstadoCuenta) -> list[CuentaCobro]:
        return self._cuentas.listar_por_estado(estado)

    def radicar(self, comando: RadicarCuenta) -> CuentaCobro:
        contrato = self._contratos.obtener_por_numero(comando.numero_contrato)
        if contrato is None or contrato.id is None:
            raise NoEncontradoError(f"No existe el contrato {comando.numero_contrato}")
        if self._cuentas.obtener_por_radicado(comando.numero_radicado) is not None:
            raise RegistroDuplicadoError(f"Ya existe el radicado {comando.numero_radicado}")
        if self._cuentas.existe_numero_cuenta(contrato.id, comando.numero_cuenta):
            raise RegistroDuplicadoError(
                f"Ya existe la cuenta {comando.numero_cuenta} "
                f"en el contrato {contrato.numero_contrato}"
            )

        cuenta = CuentaCobro(
            numero_radicado=comando.numero_radicado,
            numero_cuenta=comando.numero_cuenta,
            id_contrato=contrato.id,
            valor_cobro=ValorMonetario(comando.valor_cobro),
            concepto_pago=comando.concepto_pago,
            fecha_presentacion=comando.fecha_presentacion,
            id_usuario=comando.id_usuario,
            observaciones=comando.observaciones,
        )
        self._cuentas.guardar(cuenta)
        self._publicador.publicar(
            CuentaRadicada(
                id_usuario=comando.id_usuario,
                numero_radicado=cuenta.numero_radicado,
                id_contrato=cuenta.id_contrato,
                valor_cobro=cuenta.valor_cobro.monto,
            )
        )
        return cuenta

    def cambiar_estado(self, comando: CambiarEstadoCuenta) -> CuentaCobro:
        cuenta = self.obtener(comando.numero_radicado)
        anterior = cuenta.estado
        cuenta.cambiar_estado(comando.nuevo_estado, comando.id_usuario, comando.observacion)
        self._cuentas.guardar(cuenta)
        self._publicador.publicar(
            EstadoCuentaCambiado(
                id_usuario=comando.id_usuario,
                numero_radicado=cuenta.numero_radicado,
                estado_anterior=anterior,
                estado_nuevo=cuenta.estado,
                observacion=comando.observacion,
            )
        )
        return cuenta

    def adjuntar(self, comando: AdjuntarDocumento) -> CuentaCobro:
        cuenta = self.obtener(comando.numero_radicado)
        documento = construir_documento(comando)
        cuenta.agregar_documento(documento)
        self._cuentas.guardar(cuenta)
        self._publicador.publicar(
            DocumentoAdjuntado(
                id_usuario=comando.id_usuario,
                numero_radicado=cuenta.numero_radicado,
                nombre_original=documento.nombre_original,
                origen=documento.origen,
                tipo=documento.tipo,
            )
        )
        return cuenta
