# Responsabilidades de EventPublisher y EventSubscriber (tema 5)

**Dónde están.** `src/gestion_documental/events/publicador.py`. Las dos son clases abstractas (ABC).
- **`EventPublisher`**: registrar suscriptores (`suscribir(tipo_evento, suscriptor)`) y entregar
  eventos (`publicar(evento)`). No conoce reglas de negocio.
- **`EventSubscriber`**: reaccionar a un evento (`manejar(evento)`). No conoce al publicador ni
  a los otros suscriptores.

**Implementación.** `BusEventosEnMemoria` guarda los suscriptores por tipo y entrega de forma
síncrona. Si uno falla, lo registra con `logging` y sigue con los demás.

**Por qué separarlas.** Se puede cambiar el bus en memoria por uno real (RabbitMQ, Kafka) sin
tocar los suscriptores, y agregar suscriptores sin tocar el bus.

**Cómo se demuestra.** `test_publisher_y_subscriber_no_se_pueden_instanciar` y `test_fallo_de_un_suscriptor_no_afecta_a_los_demas`.
