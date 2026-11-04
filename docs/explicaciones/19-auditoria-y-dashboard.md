# Auditoría persistente y dashboard

**Auditoría.** `AuditoriaMongo` (`repositories/mongo.py`) es un suscriptor más del bus: hereda de
`AuditoriaPersistente` (`events/auditoria.py`), que a su vez es un `EventSubscriber`. Guarda cada
evento en la colección `auditoria`. El servicio no sabe que existe: solo publica.

**Eventos nuevos sin tocar código.** `CuentaPagada`, `CuentaAnulada`, `CuentaEditada`,
`DocumentoEliminado` y `ContratoCambiado` llegan a `RegistroAuditoria` y a `AuditoriaMongo` porque
están suscritos a `EventoDominio` y el bus recorre el MRO. `CuentaPagada` hereda de
`EstadoCuentaCambiado`, así que el notificador también la recibe.
Lo prueba `test_auditoria_recibe_eventos_nuevos_sin_cambiar_su_codigo`.

**Dashboard.** `GET /dashboard/resumen` agrupa las cuentas por estado y por contrato con la etapa
`$group` del *aggregation pipeline* de Mongo: la base suma y cuenta, y solo viajan los totales.
En memoria se calcula lo mismo en Python; la batería de repositorios comprueba que coinciden.
