# Principio de Sustitución de Liskov (tema 11)

**Qué es.** Si un código funciona con la madre, debe funcionar con cualquier hija, sin sorpresas.

**Dónde está.** Clases en `src/gestion_documental/domain/documentos.py`. Prueba en
`tests/test_documentos.py::test_lsp_cualquier_subclase_sirve_como_documento`: recorre todas
las hijas de `Documento` y les aplica la misma función `usar_como_documento()` (validar,
describir, convertir a diccionario). Otro test falla si se crea una hija y no se agrega a la prueba.

**Por qué.** `CuentaCobro.agregar_documento()` recibe "un Documento" y no pregunta de qué tipo es.

**Matiz.** `DocumentoPDF` es más exigente al *crearse* (solo PDF), pero ya creado se comporta
como cualquier documento: no lanza errores nuevos en `describir()` ni en `a_dict()`.

**Alternativa descartada.** Hijas que lanzan "no implementado" en un método de la madre.
