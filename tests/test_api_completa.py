from typing import Any

import pytest
from fastapi.middleware.cors import CORSMiddleware

from gestion_documental.api.main import app
from gestion_documental.config import ConfiguracionApi
from gestion_documental.datos_sinteticos import pdf_sintetico
from gestion_documental.domain.archivos import TAMANO_MAXIMO_BYTES
from gestion_documental.repositories.memoria import RepositorioArchivosEnMemoria
from tests.cliente_api import ClienteApi
from tests.fabricas import PERMISOS_POR_ROL

ADMIN = "administrador@example.com"
RADICADOR = "radicador@example.com"
REVISOR = "revisor@example.com"
SUPERVISOR = "supervisor@example.com"
CONSULTA = "consulta@example.com"

CUENTA: dict[str, Any] = {
    "numero_radicado": "RAD-API-0001",
    "numero_cuenta": "CUENTA-001",
    "numero_contrato": "CONT-SINT-001",
    "valor_cobro": "1500000.00",
    "concepto_pago": "Honorarios sintéticos",
    "fecha_presentacion": "2026-01-31",
}

ENDPOINTS: list[tuple[str, str, str | None]] = [
    ("GET", "/usuarios", "usuarios.gestionar"),
    ("POST", "/usuarios", "usuarios.gestionar"),
    ("POST", "/usuarios/x/reiniciar-bloqueo", "usuarios.gestionar"),
    ("GET", "/contratistas", "contratistas.consultar"),
    ("POST", "/contratistas", "contratistas.gestionar"),
    ("POST", "/contratistas/x/desactivar", "contratistas.gestionar"),
    ("GET", "/contratos", "contratos.consultar"),
    ("POST", "/contratos", "contratos.gestionar"),
    ("POST", "/contratos/CONT-SINT-001/estado", "contratos.gestionar"),
    ("POST", "/cuentas", "cuentas.radicar"),
    ("GET", "/cuentas", "cuentas.consultar"),
    ("GET", "/cuentas/RAD-X/historial", "cuentas.consultar"),
    ("PATCH", "/cuentas/RAD-X", "cuentas.editar"),
    ("POST", "/cuentas/RAD-X/estado", "cuentas.cambiar_estado"),
    ("POST", "/cuentas/RAD-X/anular", "cuentas.cambiar_estado"),
    ("POST", "/cuentas/RAD-X/pagar", "cuentas.pagar"),
    ("POST", "/cuentas/RAD-X/documentos/url", "documentos.adjuntar"),
    ("GET", "/cuentas/RAD-X/documentos/d1/descarga", "documentos.consultar"),
    ("DELETE", "/cuentas/RAD-X/documentos/d1", "documentos.eliminar"),
    ("GET", "/dashboard/resumen", "cuentas.consultar"),
    ("GET", "/auditoria", None),
]


def casos_de_permiso() -> list[Any]:
    casos = []
    for metodo, ruta, permiso in ENDPOINTS:
        for rol, permisos in PERMISOS_POR_ROL.items():
            permitido = rol == "Administrador" if permiso is None else permiso in permisos
            casos.append(pytest.param(metodo, ruta, rol, permitido, id=f"{rol}-{metodo}-{ruta}"))
    return casos


@pytest.mark.parametrize(("metodo", "ruta", "rol", "permitido"), casos_de_permiso())
def test_permisos_por_rol(
    api: ClienteApi, metodo: str, ruta: str, rol: str, permitido: bool
) -> None:
    respuesta = api.http.request(
        metodo, ruta, json={}, headers=api.cabeceras(f"{rol.lower()}@example.com")
    )

    if permitido:
        assert respuesta.status_code != 403, respuesta.text
    else:
        assert respuesta.status_code == 403
        assert respuesta.json()["error"] == "PERMISO_DENEGADO"


def radicar(api: ClienteApi, **cambios: Any) -> Any:
    return api.http.post("/cuentas", json={**CUENTA, **cambios}, headers=api.cabeceras(RADICADOR))


def subir(api: ClienteApi, contenido: bytes, nombre: str = "soporte.pdf") -> Any:
    return api.http.post(
        "/cuentas/RAD-API-0001/documentos",
        files={"archivo": (nombre, contenido, "application/octet-stream")},
        data={"tipo": "CERTIFICADO"},
        headers=api.cabeceras(RADICADOR),
    )


def test_error_uniforme_en_404_401_y_422(api: ClienteApi) -> None:
    sin_ruta = api.http.get("/no-existe")
    sin_token = api.http.get("/cuentas")
    invalido = radicar(api, valor_cobro="-5")

    assert sin_ruta.json() == {"error": "NO_ENCONTRADO", "detalle": "Not Found"}
    assert sin_token.status_code == 401
    assert sin_token.json()["error"] == "NO_AUTENTICADO"
    assert invalido.status_code == 422
    assert invalido.json()["error"] == "VALIDACION"
    assert "valor_cobro" in invalido.json()["detalle"]


def test_cors_lee_origenes_de_la_configuracion() -> None:
    configuracion = ConfiguracionApi(cors_origins="http://localhost:3000, https://ejemplo.app")

    assert configuracion.origenes == ["http://localhost:3000", "https://ejemplo.app"]
    assert any(getattr(m, "cls", None) is CORSMiddleware for m in app.user_middleware)


def test_openapi_agrupa_por_modulo(api: ClienteApi) -> None:
    etiquetas = {e["name"] for e in api.http.get("/openapi.json").json()["tags"]}

    assert {"auth", "usuarios", "contratistas", "contratos", "cuentas", "documentos"} <= etiquetas
    assert {"auditoria", "dashboard", "sistema"} <= etiquetas


def test_usuarios_crud_sin_borrado(api: ClienteApi) -> None:
    cabeceras = api.cabeceras(ADMIN)
    creado = api.http.post(
        "/usuarios",
        json={
            "nombre": "Nuevo",
            "apellido": "Sintético",
            "correo": "nuevo2@example.com",
            "cargo": "Auxiliar",
            "rol": "Consulta",
        },
        headers=cabeceras,
    )
    assert creado.status_code == 201
    cuerpo = creado.json()
    id_usuario = cuerpo["usuario"]["id"]
    assert cuerpo["usuario"]["debe_cambiar_contrasena"] is True

    login = api.login("nuevo2@example.com", cuerpo["contrasena_temporal"])
    assert login.status_code == 200
    editado = api.http.patch(f"/usuarios/{id_usuario}", json={"cargo": "Jefe"}, headers=cabeceras)
    con_rol = api.http.put(
        f"/usuarios/{id_usuario}/rol", json={"rol": "Revisor"}, headers=cabeceras
    )
    desactivado = api.http.post(f"/usuarios/{id_usuario}/desactivar", headers=cabeceras)
    listado = api.http.get("/usuarios", headers=cabeceras)

    assert editado.json()["cargo"] == "Jefe"
    assert con_rol.json()["rol"] == "Revisor"
    assert desactivado.json()["activo"] is False
    assert "nuevo2@example.com" in [u["correo"] for u in listado.json()]
    assert api.http.delete(f"/usuarios/{id_usuario}", headers=cabeceras).status_code == 405
    assert api.http.get("/usuarios/64c000000000000000000099", headers=cabeceras).status_code == 404


def test_reiniciar_bloqueo(api: ClienteApi) -> None:
    for _ in range(5):
        api.login(CONSULTA, "equivocada")
    assert api.login(CONSULTA).status_code == 403
    id_consulta = api.escenario.id_de(CONSULTA)

    respuesta = api.http.post(
        f"/usuarios/{id_consulta}/reiniciar-bloqueo", headers=api.cabeceras(ADMIN)
    )

    assert respuesta.json()["intentos_fallidos"] == 0
    assert api.login(CONSULTA).status_code == 200


def test_contratistas_crud_y_busqueda(api: ClienteApi) -> None:
    cabeceras = api.cabeceras(ADMIN)
    creado = api.http.post(
        "/contratistas",
        json={
            "tipo_persona": "NATURAL",
            "nombre_completo": "Ana Sintética",
            "nit_cedula": "52000001",
        },
        headers=cabeceras,
    )
    id_contratista = creado.json()["id"]

    editado = api.http.patch(
        f"/contratistas/{id_contratista}", json={"telefono": "3000000000"}, headers=cabeceras
    )
    obtenido = api.http.get(f"/contratistas/{id_contratista}", headers=api.cabeceras(CONSULTA))
    desactivado = api.http.post(f"/contratistas/{id_contratista}/desactivar", headers=cabeceras)
    busqueda = api.http.get("/contratistas", params={"q": "ana"}, headers=cabeceras)
    activos = api.http.get("/contratistas", params={"solo_activos": True}, headers=cabeceras)
    duplicado = api.http.post(
        "/contratistas",
        json={"tipo_persona": "NATURAL", "nombre_completo": "Otra", "nit_cedula": "52000001"},
        headers=cabeceras,
    )
    nit_invalido = api.http.post(
        "/contratistas",
        json={"tipo_persona": "JURIDICA", "nombre_completo": "X", "nit_cedula": "900000001-9"},
        headers=cabeceras,
    )

    assert creado.status_code == 201
    assert editado.json()["telefono"] == "3000000000"
    assert obtenido.json()["nombre_completo"] == "Ana Sintética"
    assert desactivado.json()["activo"] is False
    assert [c["nombre_completo"] for c in busqueda.json()] == ["Ana Sintética"]
    assert [c["nit_cedula"] for c in activos.json()] == ["900000001-2"]
    assert duplicado.status_code == 409
    assert nit_invalido.json()["error"] == "ERROR_DE_NEGOCIO"


def test_contratos_crud_y_estado(api: ClienteApi) -> None:
    cabeceras = api.cabeceras(ADMIN)
    datos = {
        "numero_contrato": "CONT-NUEVO",
        "nit_contratista": "900000001-2",
        "objeto_contrato": "Objeto sintético",
        "valor_total": "5000000.00",
        "fecha_inicio": "2026-01-01",
        "fecha_fin": "2026-06-30",
        "id_supervisor": api.escenario.id_de(SUPERVISOR),
    }

    creado = api.http.post("/contratos", json=datos, headers=cabeceras)
    editado = api.http.patch(
        "/contratos/CONT-NUEVO", json={"objeto_contrato": "Objeto editado"}, headers=cabeceras
    )
    suspendido = api.http.post(
        "/contratos/CONT-NUEVO/estado", json={"nuevo_estado": "SUSPENDIDO"}, headers=cabeceras
    )
    invalido = api.http.post(
        "/contratos/CONT-NUEVO/estado", json={"nuevo_estado": "LIQUIDADO"}, headers=cabeceras
    )
    supervisor_malo = api.http.post(
        "/contratos",
        json={
            **datos,
            "numero_contrato": "CONT-2",
            "id_supervisor": api.escenario.id_de(RADICADOR),
        },
        headers=cabeceras,
    )
    listado = api.http.get(
        "/contratos", params={"estado": "SUSPENDIDO"}, headers=api.cabeceras(CONSULTA)
    )

    assert creado.status_code == 201
    assert editado.json()["objeto_contrato"] == "Objeto editado"
    assert suspendido.json()["estado"] == "SUSPENDIDO"
    assert invalido.status_code == 409
    assert supervisor_malo.json() == {
        "error": "ERROR_DE_NEGOCIO",
        "detalle": "El supervisor debe tener el rol Supervisor",
    }
    assert [c["numero_contrato"] for c in listado.json()] == ["CONT-NUEVO"]


def test_cuentas_editar_anular_pagar_historial(api: ClienteApi) -> None:
    radicar(api)
    radicar(api, numero_radicado="RAD-API-0002", numero_cuenta="C-2")
    admin = api.cabeceras(ADMIN)

    editada = api.http.patch(
        "/cuentas/RAD-API-0001",
        json={"valor_cobro": "2000000.00"},
        headers=api.cabeceras(RADICADOR),
    )
    for estado in ("EN_REVISION", "APROBADA"):
        api.http.post("/cuentas/RAD-API-0001/estado", json={"nuevo_estado": estado}, headers=admin)
    pagada = api.http.post(
        "/cuentas/RAD-API-0001/pagar", json={"observacion": "Giro"}, headers=admin
    )
    anulada = api.http.post("/cuentas/RAD-API-0002/anular", json={}, headers=admin)
    historial = api.http.get("/cuentas/RAD-API-0001/historial", headers=api.cabeceras(CONSULTA))
    no_editable = api.http.patch(
        "/cuentas/RAD-API-0001", json={"concepto_pago": "x"}, headers=api.cabeceras(RADICADOR)
    )
    sobre_tope = radicar(
        api, numero_radicado="RAD-3", numero_cuenta="C-3", valor_cobro="9000000.00"
    )

    assert editada.json()["valor_cobro"] == "2000000.00"
    assert pagada.json()["estado"] == "PAGADA"
    assert anulada.json()["estado"] == "ANULADA"
    assert [c["estado_nuevo"] for c in historial.json()] == [
        "RECIBIDA",
        "EN_REVISION",
        "APROBADA",
        "PAGADA",
    ]
    assert no_editable.status_code == 400
    assert sobre_tope.status_code == 400
    assert "saldo" in sobre_tope.json()["detalle"]


def test_listado_con_filtros_y_paginacion(api: ClienteApi) -> None:
    for indice in range(1, 4):
        radicar(
            api,
            numero_radicado=f"RAD-{indice}",
            numero_cuenta=f"C-{indice}",
            valor_cobro="100.00",
            fecha_presentacion=f"2026-0{indice}-15",
        )
    cabeceras = api.cabeceras(CONSULTA)

    pagina = api.http.get("/cuentas", params={"pagina": 2, "tamano": 2}, headers=cabeceras).json()
    filtrada = api.http.get(
        "/cuentas",
        params={
            "numero_contrato": "CONT-SINT-001",
            "nit_contratista": "900000001-2",
            "desde": "2026-02-01",
            "estado": "RECIBIDA",
        },
        headers=cabeceras,
    ).json()

    assert (pagina["total"], [c["numero_radicado"] for c in pagina["items"]]) == (3, ["RAD-3"])
    assert [c["numero_radicado"] for c in filtrada["items"]] == ["RAD-2", "RAD-3"]


def test_documentos_subir_descargar_y_eliminar(api: ClienteApi) -> None:
    radicar(api)
    contenido = pdf_sintetico("Soporte sintético")

    subido = subir(api, contenido, "soporte.png")
    id_documento = subido.json()["id_documento"]
    descarga = api.http.get(
        f"/cuentas/RAD-API-0001/documentos/{id_documento}/descarga",
        headers=api.cabeceras(CONSULTA),
    )
    eliminado = api.http.delete(
        f"/cuentas/RAD-API-0001/documentos/{id_documento}", headers=api.cabeceras(RADICADOR)
    )
    tras_eliminar = api.http.get(
        f"/cuentas/RAD-API-0001/documentos/{id_documento}/descarga",
        headers=api.cabeceras(CONSULTA),
    )

    assert subido.status_code == 201
    assert subido.json()["tipo_mime"] == "application/pdf"
    assert "PDF" in subido.json()["descripcion"]
    assert descarga.content == contenido
    assert descarga.headers["content-type"] == "application/pdf"
    assert "soporte.png" in descarga.headers["content-disposition"]
    assert eliminado.status_code == 204
    assert tras_eliminar.status_code == 404


def test_descarga_con_hash_alterado_da_409(api: ClienteApi) -> None:
    radicar(api)
    subido = subir(api, pdf_sintetico("Original")).json()
    archivos = api.escenario.repos.archivos
    assert isinstance(archivos, RepositorioArchivosEnMemoria)
    archivos.reemplazar(subido["ruta_archivo"], pdf_sintetico("Alterado"))

    respuesta = api.http.get(
        f"/cuentas/RAD-API-0001/documentos/{subido['id_documento']}/descarga",
        headers=api.cabeceras(CONSULTA),
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"] == "INTEGRIDAD_DEL_ARCHIVO"


def test_subida_rechaza_tipo_y_tamano(api: ClienteApi) -> None:
    radicar(api)

    ejecutable = subir(api, b"MZ\x90\x00 ejecutable", "factura.pdf")
    grande = subir(api, b"%PDF-" + b"0" * TAMANO_MAXIMO_BYTES)

    assert ejecutable.status_code == 400
    assert ejecutable.json()["error"] == "ARCHIVO_INVALIDO"
    assert grande.status_code == 413
    assert grande.json()["error"] == "ARCHIVO_DEMASIADO_GRANDE"


def test_adjuntar_por_url(api: ClienteApi) -> None:
    radicar(api)

    respuesta = api.http.post(
        "/cuentas/RAD-API-0001/documentos/url",
        json={"nombre_original": "rut.pdf", "url": "https://example.com/rut.pdf", "tipo": "RUT"},
        headers=api.cabeceras(RADICADOR),
    )
    sin_esquema = api.http.post(
        "/cuentas/RAD-API-0001/documentos/url",
        json={"nombre_original": "rut.pdf", "url": "ftp://example.com/rut.pdf", "tipo": "RUT"},
        headers=api.cabeceras(RADICADOR),
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["documentos"][0]["origen"] == "URL"
    assert sin_esquema.status_code == 422


def test_auditoria_solo_administrador_y_con_filtros(api: ClienteApi) -> None:
    radicar(api)
    api.http.post("/cuentas/RAD-API-0001/anular", json={}, headers=api.cabeceras(ADMIN))

    todos = api.http.get("/auditoria", headers=api.cabeceras(ADMIN)).json()
    anuladas = api.http.get(
        "/auditoria", params={"tipo": "CuentaAnulada"}, headers=api.cabeceras(ADMIN)
    ).json()

    assert [e["tipo"] for e in todos] == ["CuentaAnulada", "CuentaRadicada"]
    assert len(anuladas) == 1
    assert anuladas[0]["datos"]["estado_nuevo"] == "ANULADA"


def test_dashboard_resumen(api: ClienteApi) -> None:
    radicar(api)
    radicar(api, numero_radicado="RAD-API-0002", numero_cuenta="C-2", valor_cobro="500.50")

    resumen = api.http.get("/dashboard/resumen", headers=api.cabeceras(CONSULTA)).json()

    assert resumen["por_estado"] == [{"clave": "RECIBIDA", "cantidad": 2, "total": "1500500.50"}]
    assert resumen["por_contrato"][0]["clave"] == "CONT-SINT-001"
