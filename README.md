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
copy .env.example .env      # completa MONGO_URI, MONGO_DB y JWT_SECRET
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

Todas las rutas de `/cuentas` exigen un token. En http://127.0.0.1:8000/docs pulsa
*Authorize* e ingresa un correo del seed (por ejemplo `ana.rodriguez@entidad.gov.co`) con la
contraseña `Demo2025*`. El seed imprime la lista de usuarios y sus roles.

| Método | Ruta | Permiso | Descripción |
|--------|------|---------|-------------|
| GET | `/health` | — | Estado de la API y de la BD (200 o 503) |
| POST | `/auth/login` | — | Formulario OAuth2 (`username` = correo, `password`); devuelve el token |
| GET | `/auth/me` | token | Usuario, rol y permisos |
| POST | `/auth/cambiar-contrasena` | token | Obligatorio si el usuario debe cambiarla; hasta entonces el resto responde 403 |
| POST | `/cuentas` | `cuentas.radicar` | Radica una cuenta (201; 404 contrato inexistente; 409 duplicada) |
| GET | `/cuentas/{radicado}` | `cuentas.consultar` | Cuenta con documentos e historial |
| POST | `/cuentas/{radicado}/estado` | `cuentas.cambiar_estado` (+ `cuentas.pagar` para PAGADA) | Cambia el estado (409 si la transición no es válida) |
| GET | `/cuentas?estado=RECIBIDA` | `cuentas.consultar` | Lista las cuentas en un estado |

Códigos: 401 sin token o token inválido, 403 sin permiso, usuario inactivo o bloqueado (5 intentos
fallidos bloquean 15 minutos). El usuario de cada operación se toma del token, no del cuerpo.

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
