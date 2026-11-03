# Herencia: simple, jerárquica, multinivel y múltiple (temas 8 y 9)

**Qué es.** Una hija recibe datos y métodos de su madre. Todo en `src/gestion_documental/domain/`.

- **Simple:** una hija, una madre. `DocumentoURL(Documento)` en `documentos.py`.
- **Jerárquica:** varias hijas de la misma madre. `DocumentoLocal` y `DocumentoURL` de
  `Documento`; `PersonaNatural` y `PersonaJuridica` de `Contratista` (`contratistas.py`).
- **Multinivel:** `DocumentoPDF` → `DocumentoLocal` → `Documento`. Un PDF cumple las reglas
  de un archivo local y además exige `application/pdf`.
- **Múltiple:** `Contratista(AuditableMixin, ABC)`. `AuditableMixin` (`mixins.py`) aporta quién y
  cuándo creó o modificó. El orden de búsqueda de métodos (MRO) se prueba en
  `tests/test_contratistas.py::test_mro_del_mixin`.

**Por qué.** Cada nivel agrega una regla real del negocio sin repetir código.
**Alternativa descartada.** Copiar los campos de auditoría en cada clase en vez del mixin.
