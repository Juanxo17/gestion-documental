# Arquitectura basada en eventos, EDA (tema 4)

**Qué es.** En vez de que una parte del sistema llame directamente a todas las demás, anuncia
"pasó algo" (un evento) y las partes interesadas reaccionan. Quien anuncia no sabe quién escucha.

**Dónde está.** `src/gestion_documental/events/`: los hechos están en `eventos.py`
(`CuentaRadicada`, `EstadoCuentaCambiado`, `DocumentoAdjuntado`), el canal en `publicador.py`
(`BusEventosEnMemoria`) y las reacciones en `suscriptores.py` (`RegistroAuditoria`,
`NotificadorSupervisor`). En el módulo 4 el servicio publicará estos eventos tras guardar.

**Por qué.** Agregar una reacción nueva (enviar un correo, actualizar un tablero) es crear un
suscriptor y registrarlo; el código que radica cuentas no se toca.

**Alternativa descartada.** Que el servicio llame en orden a auditoría, notificación, etc.:
cada reacción nueva obligaría a modificarlo y un fallo en una cortaría las siguientes.
