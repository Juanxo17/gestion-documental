# Componentes de la base de datos del proyecto (tema 3)

**Colecciones.** `roles`, `usuarios`, `contratistas`, `contratos` y `cuentas_cobro`, a partir de
las 12 tablas de `docs/db/script_bd.sql`; la traducción está en `docs/db/mapeo-mongo.md`.

**Embebido o referencia.** Se *embebe* lo que solo existe dentro de su dueño y se lee con él: los
permisos dentro del rol, y los documentos y el historial dentro de la cuenta de cobro (una sola
lectura trae todo). Se *referencia* por `_id` lo que tiene vida propia: el contrato de una cuenta,
el contratista de un contrato, el usuario que radicó.

**Índices.** `src/gestion_documental/repositories/indices.py`, `crear_indices()`: únicos para las
llaves naturales (radicado, correo, NIT/cédula, número de contrato, nombre de rol) y el compuesto
`(id_contrato, numero_cuenta)`. Reemplazan los `UNIQUE` del SQL; los `CHECK` pasaron al dominio.

**Cómo se demuestra.** `scripts/seed.py` carga los datos; `tests/test_indices.py` (integración).
