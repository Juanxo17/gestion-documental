import hashlib
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from gestion_documental.domain.archivos import sha256, validar_archivo
from gestion_documental.domain.cuenta_cobro import CambioEstado, CuentaCobro
from gestion_documental.domain.documentos import (
    MIME_PDF,
    Documento,
    DocumentoLocal,
    DocumentoPDF,
    DocumentoURL,
)
from gestion_documental.domain.enums import EstadoCuenta, OrigenDocumento
from gestion_documental.domain.errores import ErrorDominio, NoEncontradoError
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.events.comandos import (
    AdjuntarArchivo,
    AdjuntarDocumento,
    CambiarEstadoCuenta,
    EditarCuenta,
    RadicarCuenta,
)
from gestion_documental.events.eventos import (
    CuentaAnulada,
    CuentaEditada,
    CuentaPagada,
    CuentaRadicada,
    DocumentoAdjuntado,
    DocumentoEliminado,
    EstadoCuentaCambiado,
)
from gestion_documental.events.publicador import EventPublisher
from gestion_documental.repositories.base import (
    FiltroCuentas,
    RegistroDuplicadoError,
    RepositorioArchivos,
    RepositorioContratistas,
    RepositorioContratos,
    RepositorioCuentas,
    ResumenGrupo,
)

__all__ = ["IntegridadArchivoError", "NoEncontradoError", "ServicioCuentas"]

EVENTO_POR_ESTADO: dict[EstadoCuenta, type[EstadoCuentaCambiado]] = {
    EstadoCuenta.PAGADA: CuentaPagada,
    EstadoCuenta.ANULADA: CuentaAnulada,
}


class IntegridadArchivoError(Exception):
    pass


@dataclass(frozen=True)
class PaginaCuentas:
    items: list[CuentaCobro]
    total: int
    pagina: int
    tamano: int


@dataclass(frozen=True)
class ResumenDashboard:
    por_estado: list[ResumenGrupo]
    por_contrato: list[ResumenGrupo]


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
        contratistas: RepositorioContratistas,
        archivos: RepositorioArchivos,
        publicador: EventPublisher,
    ) -> None:
        self._cuentas = cuentas
        self._contratos = contratos
        self._contratistas = contratistas
        self._archivos = archivos
        self._publicador = publicador

    def obtener(self, numero_radicado: str) -> CuentaCobro:
        cuenta = self._cuentas.obtener_por_radicado(numero_radicado)
        if cuenta is None:
            raise NoEncontradoError(f"No existe la cuenta con radicado {numero_radicado}")
        return cuenta

    def historial(self, numero_radicado: str) -> tuple[CambioEstado, ...]:
        return self.obtener(numero_radicado).historial

    def listar_por_estado(self, estado: EstadoCuenta) -> list[CuentaCobro]:
        return self._cuentas.listar_por_estado(estado)

    def buscar(
        self,
        *,
        estado: EstadoCuenta | None = None,
        numero_contrato: str | None = None,
        nit_contratista: str | None = None,
        desde: date | None = None,
        hasta: date | None = None,
        pagina: int = 1,
        tamano: int = 20,
    ) -> PaginaCuentas:
        ids_contrato: set[str] | None = None
        if numero_contrato is not None:
            contrato = self._contratos.obtener_por_numero(numero_contrato)
            ids_contrato = {contrato.id} if contrato is not None and contrato.id else set()
        if nit_contratista is not None:
            contratista = self._contratistas.obtener_por_identificacion(nit_contratista)
            del_contratista = (
                {c.id for c in self._contratos.listar(contratista.id) if c.id}
                if contratista is not None and contratista.id
                else set()
            )
            ids_contrato = (
                del_contratista if ids_contrato is None else ids_contrato & del_contratista
            )
        filtro = FiltroCuentas(
            estado=estado,
            ids_contrato=None if ids_contrato is None else tuple(sorted(ids_contrato)),
            desde=desde,
            hasta=hasta,
        )
        items, total = self._cuentas.buscar(filtro, pagina, tamano)
        return PaginaCuentas(items=items, total=total, pagina=pagina, tamano=tamano)

    def radicar(self, comando: RadicarCuenta) -> CuentaCobro:
        contrato = self._contratos.obtener_por_numero(comando.numero_contrato)
        if contrato is None or contrato.id is None:
            raise NoEncontradoError(f"No existe el contrato {comando.numero_contrato}")
        contrato.verificar_radicacion(comando.fecha_presentacion)
        if self._cuentas.obtener_por_radicado(comando.numero_radicado) is not None:
            raise RegistroDuplicadoError(f"Ya existe el radicado {comando.numero_radicado}")
        if self._cuentas.existe_numero_cuenta(contrato.id, comando.numero_cuenta):
            raise RegistroDuplicadoError(
                f"Ya existe la cuenta {comando.numero_cuenta} "
                f"en el contrato {contrato.numero_contrato}"
            )
        self._verificar_tope(contrato.id, comando.valor_cobro)

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

    def editar(self, comando: EditarCuenta) -> CuentaCobro:
        cuenta = self.obtener(comando.numero_radicado)
        cuenta.verificar_editable()
        if (
            comando.numero_cuenta is not None
            and comando.numero_cuenta != cuenta.numero_cuenta
            and self._cuentas.existe_numero_cuenta(cuenta.id_contrato, comando.numero_cuenta)
        ):
            raise RegistroDuplicadoError(
                f"Ya existe la cuenta {comando.numero_cuenta} en el contrato"
            )
        if comando.valor_cobro is not None:
            self._verificar_tope(cuenta.id_contrato, comando.valor_cobro, cuenta.numero_radicado)
        if comando.fecha_presentacion is not None:
            contrato = self._contratos.obtener_por_id(cuenta.id_contrato)
            if contrato is not None and not contrato.esta_vigente(comando.fecha_presentacion):
                raise ErrorDominio("La nueva fecha está fuera de la vigencia del contrato")
        campos = cuenta.editar(
            numero_cuenta=comando.numero_cuenta,
            valor_cobro=None
            if comando.valor_cobro is None
            else ValorMonetario(comando.valor_cobro),
            concepto_pago=comando.concepto_pago,
            fecha_presentacion=comando.fecha_presentacion,
            observaciones=comando.observaciones,
        )
        if not campos:
            return cuenta
        self._cuentas.guardar(cuenta)
        self._publicador.publicar(
            CuentaEditada(
                id_usuario=comando.id_usuario,
                numero_radicado=cuenta.numero_radicado,
                campos=tuple(campos),
            )
        )
        return cuenta

    def cambiar_estado(self, comando: CambiarEstadoCuenta) -> CuentaCobro:
        cuenta = self.obtener(comando.numero_radicado)
        anterior = cuenta.estado
        cuenta.cambiar_estado(comando.nuevo_estado, comando.id_usuario, comando.observacion)
        self._cuentas.guardar(cuenta)
        clase_evento = EVENTO_POR_ESTADO.get(cuenta.estado, EstadoCuentaCambiado)
        self._publicador.publicar(
            clase_evento(
                id_usuario=comando.id_usuario,
                numero_radicado=cuenta.numero_radicado,
                estado_anterior=anterior,
                estado_nuevo=cuenta.estado,
                observacion=comando.observacion,
            )
        )
        return cuenta

    def anular(self, numero_radicado: str, id_usuario: str, observacion: str | None) -> CuentaCobro:
        return self.cambiar_estado(
            CambiarEstadoCuenta(
                id_usuario=id_usuario,
                numero_radicado=numero_radicado,
                nuevo_estado=EstadoCuenta.ANULADA,
                observacion=observacion,
            )
        )

    def pagar(self, numero_radicado: str, id_usuario: str, observacion: str | None) -> CuentaCobro:
        return self.cambiar_estado(
            CambiarEstadoCuenta(
                id_usuario=id_usuario,
                numero_radicado=numero_radicado,
                nuevo_estado=EstadoCuenta.PAGADA,
                observacion=observacion,
            )
        )

    def adjuntar(self, comando: AdjuntarDocumento) -> CuentaCobro:
        cuenta = self.obtener(comando.numero_radicado)
        documento = construir_documento(comando)
        cuenta.agregar_documento(documento)
        self._cuentas.guardar(cuenta)
        self._publicar_adjunto(comando.id_usuario, cuenta, documento)
        return cuenta

    def adjuntar_archivo(self, comando: AdjuntarArchivo, contenido: bytes) -> Documento:
        cuenta = self.obtener(comando.numero_radicado)
        tipo_mime = validar_archivo(contenido)
        id_archivo = self._archivos.guardar(comando.nombre_original, contenido, tipo_mime)
        clase = DocumentoPDF if tipo_mime == MIME_PDF else DocumentoLocal
        try:
            documento = clase(
                nombre_original=comando.nombre_original,
                ruta_archivo=id_archivo,
                tipo=comando.tipo,
                id_usuario=comando.id_usuario,
                tipo_mime=tipo_mime,
                hash_sha256=sha256(contenido),
                tamano_bytes=len(contenido),
            )
            cuenta.agregar_documento(documento)
            self._cuentas.guardar(cuenta)
        except Exception:
            self._archivos.eliminar(id_archivo)
            raise
        self._publicar_adjunto(comando.id_usuario, cuenta, documento)
        return documento

    def descargar(
        self, numero_radicado: str, id_documento: str
    ) -> tuple[DocumentoLocal, Iterator[bytes]]:
        documento = self.obtener(numero_radicado).documento(id_documento)
        if not isinstance(documento, DocumentoLocal):
            raise ErrorDominio("El documento es un enlace externo; se consulta en su URL")
        calculado = hashlib.sha256()
        for bloque in self._archivos.leer_bloques(documento.ruta_archivo):
            calculado.update(bloque)
        if calculado.hexdigest() != documento.hash_sha256:
            raise IntegridadArchivoError(
                f"El archivo {documento.nombre_original} no coincide con su hash registrado"
            )
        return documento, self._archivos.leer_bloques(documento.ruta_archivo)

    def eliminar_documento(
        self, numero_radicado: str, id_documento: str, id_usuario: str
    ) -> Documento:
        cuenta = self.obtener(numero_radicado)
        documento = cuenta.eliminar_documento(id_documento)
        self._cuentas.guardar(cuenta)
        if isinstance(documento, DocumentoLocal):
            self._archivos.eliminar(documento.ruta_archivo)
        self._publicador.publicar(
            DocumentoEliminado(
                id_usuario=id_usuario,
                numero_radicado=numero_radicado,
                id_documento=documento.id_documento,
                nombre_original=documento.nombre_original,
            )
        )
        return documento

    def resumen(self) -> ResumenDashboard:
        por_contrato = []
        for grupo in self._cuentas.resumen_por_contrato():
            contrato = self._contratos.obtener_por_id(grupo.clave)
            numero = contrato.numero_contrato if contrato is not None else grupo.clave
            por_contrato.append(ResumenGrupo(numero, grupo.cantidad, grupo.total))
        return ResumenDashboard(
            por_estado=self._cuentas.resumen_por_estado(), por_contrato=por_contrato
        )

    def _verificar_tope(
        self, id_contrato: str, valor: Decimal, excluir_radicado: str | None = None
    ) -> None:
        contrato = self._contratos.obtener_por_id(id_contrato)
        if contrato is None:
            raise NoEncontradoError("La cuenta apunta a un contrato que no existe")
        comprometido = self._cuentas.suma_comprometida(id_contrato, excluir_radicado)
        disponible = contrato.valor_total.monto - comprometido
        if valor > disponible:
            raise ErrorDominio(
                f"El valor supera el saldo del contrato {contrato.numero_contrato}: "
                f"disponible {disponible}"
            )

    def _publicar_adjunto(self, id_usuario: str, cuenta: CuentaCobro, documento: Documento) -> None:
        self._publicador.publicar(
            DocumentoAdjuntado(
                id_usuario=id_usuario,
                numero_radicado=cuenta.numero_radicado,
                nombre_original=documento.nombre_original,
                origen=documento.origen,
                tipo=documento.tipo,
            )
        )
