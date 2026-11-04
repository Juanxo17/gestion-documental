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
copy .env.example .env      # y completa MONGO_URI y MONGO_DB
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

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/health` | Estado de la API y de la BD (200 o 503) |
| POST | `/cuentas` | Radica una cuenta (201; 404 si el contrato no existe; 409 si está duplicada) |
| GET | `/cuentas/{radicado}` | Consulta una cuenta con documentos e historial (404 si no existe) |
| POST | `/cuentas/{radicado}/estado` | Cambia el estado (409 si la transición no es válida) |
| GET | `/cuentas?estado=RECIBIDA` | Lista las cuentas en un estado |

Ejemplo de radicación, con el contrato `CONT-2025-001` del seed:

```json
{
  "id_usuario": "<_id de un usuario del seed>",
  "numero_radicado": "RAD-2026-0001",
  "numero_cuenta": "CUENTA-002",
  "numero_contrato": "CONT-2025-001",
  "valor_cobro": "1500000.00",
  "concepto_pago": "Acta parcial 2",
  "fecha_presentacion": "2026-01-31"
}
```
