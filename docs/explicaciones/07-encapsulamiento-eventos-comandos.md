# Encapsulamiento de eventos y comandos (tema 7)

**Qué es.** Un **comando** es una orden ("radica esta cuenta") y puede rechazarse. Un **evento**
es un hecho ya ocurrido ("se radicó la cuenta"). Ambos son objetos que validan sus datos al
crearse y no se pueden modificar después (inmutables).

**Dónde está.** `src/gestion_documental/events/comandos.py` (`RadicarCuenta`,
`CambiarEstadoCuenta`, `AdjuntarDocumento`) y `events/eventos.py`. Usan Pydantic con
`frozen=True` (no se cambian) y `extra="forbid"` (no aceptan campos inventados). El comando solo
lleva la intención y sus datos; quién lo ejecuta llega en el módulo 4.

**Cómo se demuestra.** `test_evento_es_inmutable`, `test_comando_es_inmutable`, `test_evento_rechaza_campos_desconocidos`.

**Por qué.** Si un evento cambiara después de publicado, dos suscriptores verían hechos distintos.
**Alternativa descartada.** Diccionarios sueltos, sin validación ni protección.
