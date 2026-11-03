# Manejo polimórfico de eventos (tema 6)

**Qué es.** Suscribirse a un tipo general y recibir también todos sus tipos particulares.
Quien escucha "cualquier evento" recibe radicaciones, cambios de estado y adjuntos.

**Dónde está.** `src/gestion_documental/events/publicador.py`, `BusEventosEnMemoria.publicar()`.
Recorre `type(evento).__mro__`, la lista de "madres" del evento
(`EstadoCuentaCambiado` → `EventoDominio` → ...), y entrega a los suscritos a cada una.

**Cómo se demuestra.** `test_auditoria_recibe_los_tres_tipos_y_notificador_solo_el_suyo` en
`tests/test_bus_eventos.py`: `RegistroAuditoria` (suscrito a `EventoDominio`) recibe los 3 tipos;
`NotificadorSupervisor` (suscrito a `EstadoCuentaCambiado`) solo ese.

**Por qué.** Un evento nuevo (p. ej. `CuentaPagada`) llega a la auditoría sin registrarlo aparte.
**Alternativa descartada.** Suscribir la auditoría tipo por tipo: es fácil olvidar uno.
