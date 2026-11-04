from datetime import date
from decimal import Decimal

from gestion_documental.domain.contrato import Contrato
from gestion_documental.domain.enums import EstadoContrato
from gestion_documental.domain.errores import ErrorDominio, NoEncontradoError
from gestion_documental.domain.usuarios import Usuario
from gestion_documental.domain.valores import ValorMonetario
from gestion_documental.events.eventos import ContratoCambiado
from gestion_documental.events.publicador import EventPublisher
from gestion_documental.repositories.base import (
    RepositorioContratistas,
    RepositorioContratos,
    RepositorioCuentas,
    RepositorioRoles,
    RepositorioUsuarios,
)

ROL_SUPERVISOR = "Supervisor"


class ServicioContratos:
    def __init__(
        self,
        contratos: RepositorioContratos,
        contratistas: RepositorioContratistas,
        usuarios: RepositorioUsuarios,
        roles: RepositorioRoles,
        cuentas: RepositorioCuentas,
        publicador: EventPublisher,
    ) -> None:
        self._contratos = contratos
        self._contratistas = contratistas
        self._usuarios = usuarios
        self._roles = roles
        self._cuentas = cuentas
        self._publicador = publicador

    def listar(self, estado: EstadoContrato | None = None) -> list[Contrato]:
        return self._contratos.listar(estado=estado)

    def supervisores(self) -> list[Usuario]:
        rol = self._roles.obtener_por_nombre(ROL_SUPERVISOR)
        if rol is None:
            return []
        return [u for u in self._usuarios.listar() if u.id_rol == rol.id and u.activo]

    def obtener(self, numero_contrato: str) -> Contrato:
        contrato = self._contratos.obtener_por_numero(numero_contrato)
        if contrato is None:
            raise NoEncontradoError(f"No existe el contrato {numero_contrato}")
        return contrato

    def crear(
        self,
        *,
        numero_contrato: str,
        nit_contratista: str,
        objeto_contrato: str,
        valor_total: Decimal,
        fecha_inicio: date,
        fecha_fin: date,
        id_supervisor: str,
    ) -> Contrato:
        contratista = self._contratistas.obtener_por_identificacion(nit_contratista)
        if contratista is None or contratista.id is None:
            raise NoEncontradoError(f"No existe el contratista {nit_contratista}")
        if not contratista.activo:
            raise ErrorDominio(f"El contratista {nit_contratista} está inactivo")
        self._verificar_supervisor(id_supervisor)
        contrato = Contrato(
            numero_contrato=numero_contrato,
            id_contratista=contratista.id,
            objeto_contrato=objeto_contrato,
            valor_total=ValorMonetario(valor_total),
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            id_supervisor=id_supervisor,
        )
        self._contratos.guardar(contrato)
        return contrato

    def editar(
        self,
        numero_contrato: str,
        *,
        objeto_contrato: str | None = None,
        valor_total: Decimal | None = None,
        fecha_inicio: date | None = None,
        fecha_fin: date | None = None,
        id_supervisor: str | None = None,
    ) -> Contrato:
        contrato = self.obtener(numero_contrato)
        if id_supervisor is not None and id_supervisor != contrato.id_supervisor:
            self._verificar_supervisor(id_supervisor)
            contrato.id_supervisor = id_supervisor
        if valor_total is not None:
            assert contrato.id is not None
            comprometido = self._cuentas.suma_comprometida(contrato.id)
            if valor_total < comprometido:
                raise ErrorDominio(
                    f"El valor total no puede ser menor que lo ya cobrado ({comprometido})"
                )
            contrato.valor_total = ValorMonetario(valor_total)
        contrato.objeto_contrato = objeto_contrato or contrato.objeto_contrato
        contrato.fecha_inicio = fecha_inicio or contrato.fecha_inicio
        contrato.fecha_fin = fecha_fin or contrato.fecha_fin
        contrato.validar()
        self._contratos.guardar(contrato)
        return contrato

    def cambiar_estado(
        self, numero_contrato: str, nuevo: EstadoContrato, id_usuario: str
    ) -> Contrato:
        contrato = self.obtener(numero_contrato)
        anterior = contrato.cambiar_estado(nuevo)
        self._contratos.guardar(contrato)
        self._publicador.publicar(
            ContratoCambiado(
                id_usuario=id_usuario,
                numero_contrato=contrato.numero_contrato,
                estado_anterior=anterior,
                estado_nuevo=contrato.estado,
            )
        )
        return contrato

    def _verificar_supervisor(self, id_supervisor: str) -> None:
        supervisor = self._usuarios.obtener_por_id(id_supervisor)
        if supervisor is None:
            raise NoEncontradoError(f"No existe el usuario supervisor {id_supervisor}")
        rol = self._roles.obtener_por_id(supervisor.id_rol)
        if rol is None or rol.nombre != ROL_SUPERVISOR:
            raise ErrorDominio("El supervisor debe tener el rol Supervisor")
        if not supervisor.activo:
            raise ErrorDominio("El supervisor está inactivo")
