# Gestión documental de cuentas de cobro

Sistema en Python para radicar cuentas de cobro de contratistas, adjuntar sus documentos y
seguir su recorrido por estados (RECIBIDA → EN_REVISION → APROBADA/RECHAZADA → PAGADA, o ANULADA).
Usa POO (jerarquías de documentos, mixins, composición), una arquitectura basada en eventos y
MongoDB Atlas. Proyecto integrador académico; todos los datos son sintéticos.

## Arquitectura

```
api/  ──▶  services/  ──▶  domain/        reglas de negocio, sin dependencias externas
              │   └──▶  repositories/      interfaz + Mongo + memoria
              └──────▶  events/            comandos, eventos, bus y suscriptores
```

Código en `src/gestion_documental/`. Cada tema del temario está ubicado en
`docs/matriz-trazabilidad.md`, con notas en `docs/explicaciones/`.

## Instalación

Requiere [uv](https://docs.astral.sh/uv/). Python 3.14 se instala solo.

```
uv sync
copy .env.example .env      # completa MONGO_URI, MONGO_DB, JWT_SECRET y CORS_ORIGINS
```

Si el DNS de tu red no resuelve URIs `mongodb+srv://`, usa la cadena larga `mongodb://` que Atlas
ofrece para versiones antiguas del driver.

## Uso

| Qué | Comando |
|-----|---------|
| Cargar datos de ejemplo en Atlas | `uv run python scripts/seed.py` |
| Demo sin red (repositorios en memoria) | `uv run python demo.py` |
| Demo contra Atlas | `uv run python demo.py --mongo` |
| API en desarrollo | `uv run fastapi dev` → http://127.0.0.1:8000/docs |
| Tests (sin red) | `uv run pytest` |
| Tests contra Atlas | `uv run pytest -m integracion` |
| Lint y tipos | `uv run ruff check .` y `uv run mypy .` |

## API

Todas las rutas, salvo `/health` y `/auth/login`, exigen un token. En
http://127.0.0.1:8000/docs pulsa *Authorize* e ingresa un correo del seed (por ejemplo
`ana.rodriguez@entidad.gov.co`, Administrador) con la contraseña `Demo2025*`. El seed imprime la
lista de usuarios y sus roles. Los endpoints están agrupados por módulo en `/docs`.

| Módulo | Rutas principales | Permisos |
|--------|-------------------|----------|
| auth | `POST /auth/login`, `GET /auth/me`, `POST /auth/cambiar-contrasena` | token |
| usuarios | `GET/POST /usuarios`, `GET/PATCH /usuarios/{id}`, `PUT /usuarios/{id}/rol`, `POST /usuarios/{id}/desactivar`, `POST /usuarios/{id}/reiniciar-bloqueo` | `usuarios.gestionar` |
| contratistas | `GET /contratistas?q=&solo_activos=`, `POST /contratistas`, `GET/PATCH /contratistas/{id}`, `POST /contratistas/{id}/desactivar` | `contratistas.consultar` / `gestionar` |
| contratos | `GET /contratos?estado=`, `POST /contratos`, `GET/PATCH /contratos/{numero}`, `POST /contratos/{numero}/estado` | `contratos.consultar` / `gestionar` |
| cuentas | `POST /cuentas`, `GET /cuentas?estado=&numero_contrato=&nit_contratista=&desde=&hasta=&pagina=&tamano=`, `GET/PATCH /cuentas/{radicado}`, `GET /cuentas/{radicado}/historial`, `POST /cuentas/{radicado}/estado`, `/anular`, `/pagar` | `cuentas.radicar`, `consultar`, `editar`, `cambiar_estado`, `pagar` |
| documentos | `POST /cuentas/{radicado}/documentos` (multipart), `POST .../documentos/url`, `GET .../documentos/{id}/descarga`, `DELETE .../documentos/{id}` | `documentos.adjuntar`, `consultar`, `eliminar` |
| auditoría | `GET /auditoria?tipo=&id_usuario=&desde=&hasta=&limite=` | solo Administrador |
| dashboard | `GET /dashboard/resumen` | `cuentas.consultar` |
| sistema | `GET /health` | — |

Todas las respuestas de error tienen la forma `{"error": "CODIGO", "detalle": "mensaje"}`:
400 regla de negocio o archivo inválido, 401 sin token, 403 sin permiso, usuario inactivo o
bloqueado, 404 no encontrado, 409 duplicado, transición inválida o archivo alterado, 413 archivo
de más de 10 MB, 422 datos con formato inválido, 503 base de datos no disponible.

Reglas principales: solo se radica contra contratos ACTIVO dentro de su vigencia; la suma de las
cuentas no anuladas ni rechazadas no puede superar el valor del contrato; una cuenta se edita
solo en RECIBIDA o EN_REVISION; los adjuntos aceptan PDF, JPG o PNG (validados por contenido) y
se guardan en GridFS con su sha256, que se verifica en cada descarga.

Ejemplo de radicación, con el contrato `CONT-2025-001` del seed:

```json
{
  "numero_radicado": "RAD-2026-0001",
  "numero_cuenta": "CUENTA-002",
  "numero_contrato": "CONT-2025-001",
  "valor_cobro": "1500000.00",
  "concepto_pago": "Acta parcial 2",
  "fecha_presentacion": "2026-01-31"
}
```
