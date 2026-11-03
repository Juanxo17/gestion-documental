# Duck typing en Python (tema 16)

**Qué es.** "Si camina y hace cuac como pato, es un pato": importa el método, no la clase.

**Dónde está.** `src/gestion_documental/events/publicador.py`: el bus acepta suscriptores de tipo
`ManejadorEventos`, un `Protocol` que solo pide `manejar(evento)`. Sirve cualquier objeto con
ese método, herede o no de `EventSubscriber`.

**Cómo se demuestra.** `test_duck_typing_suscriptor_sin_herencia` en `tests/test_bus_eventos.py`:
`ContadorPato` no hereda de nada y recibe los eventos. También `BaseDatosFalsa` en
`tests/test_health.py`, que solo tiene `command()` y reemplaza a la BD real.

**Por qué.** Se conectan objetos de otras librerías o dobles de prueba sin forzar herencia, y el
`Protocol` deja que mypy revise el método antes de ejecutar.
**Alternativa descartada.** Exigir `isinstance(suscriptor, EventSubscriber)` en `suscribir()`.
