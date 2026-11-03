# Abstracción (tema 1)

**Qué es.** Quedarse con lo esencial de una idea y esconder los detalles. Todos los
documentos tienen nombre, ruta, tipo, quién lo subió y cuándo; lo demás depende del caso.

**Dónde está.** `src/gestion_documental/domain/documentos.py`, clase `Documento`. Define lo
común y obliga a cada tipo concreto a decir cómo se valida (`validar()`) y cómo se describe
(`describir()`). `CuentaCobro` (en `domain/cuenta_cobro.py`) trabaja con "un Documento" sin
saber si es un PDF local o un enlace.

**Por qué.** Si mañana aparece un documento escaneado o firmado digitalmente, se agrega una
clase nueva y la cuenta de cobro no cambia.

**Alternativa descartada.** Una sola clase con un campo `origen` y muchos `if origen == ...`.
Cada tipo nuevo obligaría a tocar todos esos `if` y es fácil olvidar uno.
