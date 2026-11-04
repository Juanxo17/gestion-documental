from gestion_documental.domain.contratistas import Contratista
from gestion_documental.domain.enums import TipoPersona
from gestion_documental.domain.errores import NoEncontradoError
from gestion_documental.repositories.base import RepositorioContratistas
from gestion_documental.repositories.mapeo import CLASES_CONTRATISTA


class ServicioContratistas:
    def __init__(self, contratistas: RepositorioContratistas) -> None:
        self._contratistas = contratistas

    def buscar(self, texto: str | None = None, solo_activos: bool = False) -> list[Contratista]:
        return self._contratistas.buscar(texto, solo_activos)

    def obtener(self, id_contratista: str) -> Contratista:
        contratista = self._contratistas.obtener_por_id(id_contratista)
        if contratista is None:
            raise NoEncontradoError(f"No existe el contratista {id_contratista}")
        return contratista

    def crear(
        self,
        *,
        tipo_persona: TipoPersona,
        nombre_completo: str,
        nit_cedula: str,
        telefono: str | None,
        correo: str | None,
        direccion: str | None,
        id_usuario: str,
    ) -> Contratista:
        contratista = CLASES_CONTRATISTA[tipo_persona](
            nombre_completo=nombre_completo,
            nit_cedula=nit_cedula,
            telefono=telefono,
            correo=correo,
            direccion=direccion,
        )
        contratista.registrar_creacion(id_usuario)
        self._contratistas.guardar(contratista)
        return contratista

    def editar(
        self,
        id_contratista: str,
        *,
        id_usuario: str,
        nombre_completo: str | None = None,
        nit_cedula: str | None = None,
        telefono: str | None = None,
        correo: str | None = None,
        direccion: str | None = None,
    ) -> Contratista:
        contratista = self.obtener(id_contratista)
        contratista.nombre_completo = nombre_completo or contratista.nombre_completo
        contratista.nit_cedula = nit_cedula or contratista.nit_cedula
        contratista.telefono = telefono if telefono is not None else contratista.telefono
        contratista.correo = correo if correo is not None else contratista.correo
        contratista.direccion = direccion if direccion is not None else contratista.direccion
        contratista.validar()
        if contratista.creado_por is None:
            contratista.registrar_creacion(id_usuario)
        contratista.registrar_modificacion(id_usuario)
        self._contratistas.guardar(contratista)
        return contratista

    def desactivar(self, id_contratista: str, id_usuario: str) -> Contratista:
        contratista = self.obtener(id_contratista)
        if contratista.creado_por is None:
            contratista.registrar_creacion(id_usuario)
        contratista.desactivar(id_usuario)
        self._contratistas.guardar(contratista)
        return contratista
