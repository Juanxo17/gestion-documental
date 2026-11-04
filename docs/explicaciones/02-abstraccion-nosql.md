# Abstracción y bases de datos NoSQL (tema 2)

**Qué es.** El sistema pide "guarda esta cuenta" sin saber si detrás hay MongoDB o memoria.

**Dónde está.** `src/gestion_documental/repositories/base.py`: `RepositorioCuentas`,
`RepositorioContratos` y `RepositorioContratistas` (ABC). Hay dos implementaciones de cada una:
`repositories/mongo.py` (recibe la `Database` en el constructor: composición, no hereda de
`Collection`) y `repositories/memoria.py` (diccionarios). La traducción objeto ↔ documento BSON
está aislada en `repositories/mapeo.py`.

**Cómo se demuestra.** `tests/test_repositorios.py` corre la misma batería contra memoria y
contra Mongo (LSP aplicado a repositorios); ambas pasan.

**Por qué.** Los tests corren sin red y el dominio nunca importa `pymongo`.
**Alternativa descartada.** Llamar a `db.cuentas_cobro.find(...)` desde los servicios.
