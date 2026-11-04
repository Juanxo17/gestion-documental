# Proyecto Integrador: Gestión Documental

## Qué es
Sistema de gestión documental en Python con BD NoSQL (MongoDB Atlas) y
arquitectura basada en eventos (Event Driven Architecture). Contexto: gestión
de contratos y documentos de contratistas en una entidad pública (Gobernación
del Valle). Es un proyecto académico/freelance que debo sustentar y que también
será pieza de portafolio.

## Perfil del usuario y modo mentor
- He usado Python para machine learning, pero NO en POO avanzada, arquitectura
  de eventos ni desarrollo web. Next.js y front: nivel nulo, pero quiero aprender.
- Debo entregar esto completo en ~6 horas. Busco balance entre agilidad y
  aprendizaje: trabajamos por MÓDULOS (no tareas diminutas), uno por uno,
  entendiendo cada uno antes de pasar al siguiente.
- Si un módulo se pasa del tiempo estimado, propón recortar alcance en vez de
  alargarlo.
- Antes de cada concepto nuevo, explícalo en 5-10 líneas con un ejemplo mínimo
  ajeno al proyecto, y luego aplícalo.
- Claude Code escribe todo el código (dominio, eventos, repositorios, API,
  Docker, estilos) y yo lo leo.
- Cada nota de docs/explicaciones/ se escribe en lenguaje simple, para alguien
  que no domina Python: qué es, dónde está (archivo y clase exactos) y por qué.
  Máximo 15 líneas por nota.
- Al cerrar cada módulo, hazme 2-3 preguntas para comprobar que lo entendí.
  No avances hasta que responda.
- No escribas código que yo no pueda justificar en una sustentación.
- Si algo es ambiguo, pregunta antes de asumir.

## Reglas
- No modificar el esquema de BD sin preguntar.
- Cada tema del temario (docs/requisitos.md) debe tener un lugar identificable
  en el código y una nota corta en docs/explicaciones/.
- Explica el porqué antes de implementar. Un módulo por vez. Modo build por
  defecto; modo plan solo si lo pido.
- Cada módulo incluye tests. Un commit por módulo.
- Jerarquías de herencia: máximo 3 niveles. Preferir composición.
- Nunca commitear secretos. La cadena de conexión de Atlas va en .env
  (ignorado por git) y se documenta en .env.example.
- Solo datos sintéticos. Nada de datos reales de contratistas ni contratos.

## Stack
- Python: versión estable más reciente compatible con todas las dependencias
  (fijar con `uv python pin`).
- Gestor de entorno y dependencias: uv.
- Backend: FastAPI + Pydantic (eventos y comandos inmutables).
- BD: MongoDB Atlas con PyMongo (versión síncrona, para mantenerlo simple).
- Tests: pytest. Calidad: ruff (lint y formato) y mypy (tipos).
- Fase 2: frontend Next.js + TypeScript en frontend/ (despliegue en Vercel).
- Fase 3: Docker + Docker Compose, GitHub Actions (tests y lint), pre-commit.

## Comandos
- Instalar dependencias: `uv sync`
- Agregar dependencia: `uv add <paquete>` (de desarrollo: `uv add --dev <paquete>`)
- Tests sin red: `uv run pytest` (por defecto excluye el marcador `integracion`)
- Tests contra Atlas: `uv run pytest -m integracion` (usan la BD `<MONGO_DB>_pruebas` y la borran)
- Un solo test: `uv run pytest tests/test_servicio.py::test_transicion_invalida_no_guarda_ni_publica`
- Lint y formato: `uv run ruff check .` y `uv run ruff format .`
- Tipos: `uv run mypy .`
- API en desarrollo: `uv run fastapi dev` (entrypoint fijado en `[tool.fastapi]` de pyproject.toml)
- Seed (borra y recarga las 5 colecciones): `uv run python scripts/seed.py`
- Demo: `uv run python demo.py` (memoria, sin red) o `--mongo` (Atlas, requiere seed)

## Arquitectura
Layout src/: el paquete es `src/gestion_documental/`. Flujo: `api/rutas_cuentas.py` recibe un
comando Pydantic → `services/servicio_cuentas.py` valida con repositorios → dominio → `guardar`
→ publica el evento en el `EventPublisher` (solo si guardar tuvo éxito).
- Inyección: `api/dependencias.py` arma un `Repositorios` (dataclass con todos los
  repositorios, archivos GridFS y auditoría) desde `get_repositorios`, y de ahí cada servicio y
  el bus por petición. Los tests reemplazan `get_repositorios`, `get_hasher` y `get_config_auth`
  (fixture `api` en `tests/conftest.py`; datos en `tests/fabricas.py::escenario`).
- Errores: tabla `ERRORES` en `api/errores.py` (excepción → estado HTTP y código); respuesta
  uniforme `{"error", "detalle"}`. `/health` conserva su propio cuerpo.
- Auth: `api/seguridad.py` define `usuario_actual` (JWT), `usuario_habilitado` (bloquea si
  `debe_cambiar_contrasena`), `requiere_permiso(codigo)` y `requiere_rol(nombre)`. El
  `id_usuario` de los comandos sale del token. Configuración: `ConfiguracionAuth` (JWT) y
  `ConfiguracionApi` (CORS) van aparte de la de Mongo.
- Eventos: el bus de la API tiene suscritos `AuditoriaMongo` (colección `auditoria`) y el
  notificador. `CuentaPagada`/`CuentaAnulada` heredan de `EstadoCuentaCambiado`.
- Adjuntos LOCAL: contenido en GridFS, `ruta_archivo` = id de GridFS; `datos_sinteticos.py`
  genera PDFs válidos para seed, demo y tests.
- Mapeo dominio ↔ BSON solo en `repositories/mapeo.py` (ids como ObjectId, dinero Decimal128,
  fechas sin hora como datetime UTC). El dominio genera fechas con `domain/tiempo.ahora_utc()`
  (milisegundos) para que la ida y vuelta con Mongo sea exacta.
- mypy desactiva `type-abstract` porque el bus se suscribe a clases abstractas (`EventoDominio`).
- domain/: Documento y subclases, mixins, value objects
- events/: eventos y comandos (inmutables), EventPublisher, EventSubscriber
- repositories/: interfaces abstractas + implementación Mongo + una en memoria
- services/: orquestación
- api/: rutas FastAPI
- frontend/: Next.js (fase 2)
- docs/: requisitos.md, db/ (esquema entregado), matriz-trazabilidad.md,
  decisiones/, explicaciones/

## Plan de la fase 1 (~6 h)
0. Setup: estructura, .env, conexión a Atlas, /health (25 min, lo hace Claude Code)
1. Dominio: Documento abstracto, jerarquía, mixins, composición, test de LSP (75 min)
2. Eventos: eventos y comandos inmutables, EventPublisher, EventSubscriber, bus en memoria, 2 subscribers (75 min)
3. Persistencia: repositorio abstracto, implementación Mongo, implementación en memoria (50 min)
4. Servicio + API: comando -> dominio -> repo -> evento, endpoints FastAPI (50 min)
5. demo.py, tests, matriz de trazabilidad, notas en docs/explicaciones/ (45 min)
6. Simulacro de sustentación (20 min, en el proyecto de claude.ai)
Colchón: 20 min. Orden obligatorio: el dominio va antes de los eventos, y la
persistencia antes de la API.

## Fases
1. Entrega: núcleo POO + eventos + BD + demo + Docker básico.
2. Producto: API completa con autenticación y roles + frontend.
3. Portafolio: CI, despliegue, README con diagrama de arquitectura (herramienta
   candidata: https://github.com/caru-ini/stack-diagram; alternativa: Archify),
   datos de ejemplo.
Estamos en la fase 1 salvo que se indique lo contrario.