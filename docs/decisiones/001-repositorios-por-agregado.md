# 001. Un repositorio por agregado, sin repositorio genérico

**Decisión.** `repositories/base.py` define una interfaz por agregado (`RepositorioCuentas`,
`RepositorioContratos`, `RepositorioContratistas`), cada una solo con los métodos que el servicio
usa. No hay una clase `Repositorio[T]` con `crear/leer/actualizar/borrar` de la que hereden todas.

**Por qué.**
- Cada agregado se consulta distinto: las cuentas por radicado y por estado, los contratos por
  número, los contratistas por NIT o cédula. Un genérico obligaría a métodos que no se usan
  (p. ej. `borrar` contratistas, que el negocio no permite) o a filtros sueltos tipo diccionario.
- Interfaces pequeñas son más fáciles de implementar dos veces (Mongo y memoria) y de probar con
  la misma batería (`tests/test_repositorios.py`).
- Evita otra capa de herencia: la jerarquía queda en 2 niveles (interfaz → implementación).

**Costo aceptado.** Algo de código parecido entre las implementaciones Mongo (`find_one` +
función de mapeo). Es explícito y cada método se lee sin saltar a una clase base.
