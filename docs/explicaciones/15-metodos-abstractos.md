# Métodos abstractos e interfaces (tema 15)

**Qué es.** Una promesa: "toda hija debe implementar esto". La madre no se puede crear (`TypeError`).

**Dónde está.** `src/gestion_documental/domain/documentos.py`: `Documento` hereda de `ABC` y marca
`validar()` y `describir()` con `@abstractmethod`. `validar()` trae las reglas comunes y cada
hija la extiende con `super().validar()`. En `domain/contratistas.py`,
`Contratista.validar_identificacion()` es abstracta: natural valida cédula, jurídica valida NIT.

**Cómo se demuestra.** `test_documento_abstracto_no_se_puede_instanciar` y
`test_contratista_abstracto_no_se_puede_instanciar`.

**Por qué.** Si una clase nueva olvida `describir()`, el error sale al crearla, no en producción.

**Alternativa descartada.** Métodos que lanzan `NotImplementedError`: el error solo aparece al llamarlos.
