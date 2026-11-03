# Composición frente a herencia (tema 10)

**Qué es.** Herencia dice "es un" (un PDF *es un* documento). Composición dice "tiene un"
(una cuenta de cobro *tiene* documentos y un historial).

**Dónde está.** `src/gestion_documental/domain/cuenta_cobro.py`, clase `CuentaCobro`. No hereda
de nada del dominio (lo comprueba `test_cuenta_cobro_no_hereda_del_dominio`). Por dentro guarda
una lista de `Documento` y una lista de `CambioEstado`, y ofrece `agregar_documento()` y
`cambiar_estado()`. Afuera solo se entregan copias de solo lectura (tuplas).

**Por qué.** Una cuenta de cobro no *es* un documento; es un trámite que *reúne* documentos.
Así se pueden mezclar PDF y enlaces en la misma cuenta y cambiar cualquiera sin tocar la cuenta.

**Alternativa descartada.** `CuentaCobro(Documento)`: obligaría a la cuenta a tener ruta de
archivo y tipo MIME, que no tienen sentido para ella.
