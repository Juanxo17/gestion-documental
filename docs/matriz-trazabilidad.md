# Matriz de trazabilidad

Relaciona cada tema del temario (docs/requisitos.md) con el lugar del código donde se aplica.

| Tema | Decisión | Archivos | Cómo se demuestra |
|------|----------|----------|-------------------|
| 1. Abstracción en POO | `Documento` define lo común y deja a cada tipo cómo validarse y describirse | `src/gestion_documental/domain/documentos.py` | `CuentaCobro` usa `Documento` sin conocer el tipo; `docs/explicaciones/01-abstraccion.md` |
| 2. Abstracción y bases de datos NoSQL | | | |
| 3. Base de datos del Proyecto Integrador | Modelo MySQL entregado traducido a colecciones Mongo; CHECK pasan al dominio | `docs/db/script_bd.sql`, `docs/db/mapeo-mongo.md` | Tabla de CHECK → clase en `mapeo-mongo.md`; tests de `ValorMonetario`, `Contrato` y `DocumentoLocal` |
| 4. Arquitectura basada en eventos (EDA) | | | |
| 5. EventPublisher y EventSubscriber | | | |
| 6. Manejo polimórfico de eventos | | | |
| 7. Encapsulamiento de eventos y comandos | | | |
| 8. Herencia avanzada y jerarquías complejas | Jerarquía de documentos con reglas que se acumulan por nivel vía `super().validar()` | `src/gestion_documental/domain/documentos.py` | `test_pdf_hereda_reglas_de_local`; `docs/explicaciones/08-09-herencia.md` |
| 9. Herencia simple, múltiple, multinivel y jerárquica | Simple: `DocumentoURL`; jerárquica: `DocumentoLocal`/`DocumentoURL` y `PersonaNatural`/`PersonaJuridica`; multinivel: `DocumentoPDF`; múltiple: `Contratista(AuditableMixin, ABC)` | `src/gestion_documental/domain/documentos.py`, `src/gestion_documental/domain/contratistas.py`, `src/gestion_documental/domain/mixins.py` | `test_mro_del_mixin`; `docs/explicaciones/08-09-herencia.md` |
| 10. Composición frente a herencia | `CuentaCobro` tiene documentos e historial; no hereda de nada | `src/gestion_documental/domain/cuenta_cobro.py` | `test_cuenta_cobro_no_hereda_del_dominio`, `test_composicion_acepta_cualquier_documento`; `docs/explicaciones/10-composicion-vs-herencia.md` |
| 11. Principio de Sustitución de Liskov | Toda hija de `Documento` cumple el contrato de la madre | `src/gestion_documental/domain/documentos.py`, `tests/test_documentos.py` | `test_lsp_cualquier_subclase_sirve_como_documento` (parametrizado); `docs/explicaciones/11-lsp.md` |
| 12. Riesgos de jerarquías profundas | Máximo 3 niveles; lo demás con composición o mixin | `src/gestion_documental/domain/documentos.py` | `test_jerarquia_de_documento_no_supera_tres_niveles`; `docs/explicaciones/12-riesgos-jerarquias-profundas.md` |
| 13. Polimorfismo dinámico y late binding | `Documento.__post_init__` llama `self.validar()`, que se resuelve en la subclase al ejecutar (se amplía con eventos en el módulo 2) | `src/gestion_documental/domain/documentos.py` | `test_describir_se_resuelve_en_tiempo_de_ejecucion` |
| 14. Sobrescritura y despacho dinámico | Cada hija sobrescribe `validar()` y `describir()`; `DocumentoPDF.validar()` extiende con `super()` | `src/gestion_documental/domain/documentos.py` | `test_pdf_exige_mime_pdf`, `test_pdf_hereda_reglas_de_local` |
| 15. Métodos abstractos, interfaces y virtualización | `Documento` y `Contratista` son `ABC` con `@abstractmethod` | `src/gestion_documental/domain/documentos.py`, `src/gestion_documental/domain/contratistas.py` | `test_documento_abstracto_no_se_puede_instanciar`, `test_contratista_abstracto_no_se_puede_instanciar`; `docs/explicaciones/15-metodos-abstractos.md` |
| 16. Duck typing en Python | El test de salud usa una BD falsa que solo tiene `command()`, sin heredar de `Database` (se amplía en el módulo 2) | `tests/test_health.py` | `BaseDatosFalsa` en `test_health_ok_cuando_la_bd_responde` |
