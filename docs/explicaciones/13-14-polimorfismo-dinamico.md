# Polimorfismo dinámico, late binding y sobrescritura (temas 13 y 14)

**Qué es.** El mismo llamado (`evento.describir()`) ejecuta código distinto según el objeto real,
y Python decide cuál al momento de ejecutar (late binding). Cada hija **sobrescribe** el método.

**Dónde está.**
- `src/gestion_documental/events/eventos.py`: `EventoDominio.__str__` llama a `self.describir()`,
  que cada subclase sobrescribe. `RegistroAuditoria.manejar()` (`events/suscriptores.py`) escribe
  `str(evento)` sin saber de qué tipo es.
- `src/gestion_documental/domain/documentos.py`: `Documento.__post_init__` llama a `self.validar()`
  de la subclase; `DocumentoPDF.validar()` extiende la de su madre con `super()`.

**Cómo se demuestra.** `test_str_es_polimorfico` y `test_describir_se_resuelve_en_tiempo_de_ejecucion`.

**Alternativa descartada.** `if isinstance(evento, CuentaRadicada): ... elif ...` en la auditoría.
