# Riesgos de las jerarquías de herencia profundas (tema 12)

**Qué es el riesgo.** Con muchos niveles, un cambio arriba rompe cosas abajo sin que se note,
para entender una clase hay que leer todas las de arriba, y las hijas heredan cosas que no usan.

**Dónde se controla.** Regla del proyecto: máximo 3 niveles. La más larga es
`DocumentoPDF` → `DocumentoLocal` → `Documento` en `src/gestion_documental/domain/documentos.py`.
`tests/test_documentos.py::test_jerarquia_de_documento_no_supera_tres_niveles` falla si
alguien agrega un cuarto nivel.

**Cómo se evitó crecer.** Lo que no es "es un" se resolvió con composición (`CuentaCobro`) o con
un mixin pequeño (`AuditableMixin`), no con más niveles.

**Alternativa descartada.** `DocumentoPDFFirmado(DocumentoPDF)`. Si hace falta, la firma será
un objeto aparte que el documento *tiene*.
