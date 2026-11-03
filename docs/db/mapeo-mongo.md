# Mapeo del modelo relacional (script_bd.sql) a MongoDB

El diseño entregado (`script_bd.sql`, `documento_final.docx`) está escrito para MySQL 8.
Este documento fija cómo se traduce a colecciones de MongoDB sin cambiar su significado.

## Criterios

- Lo que siempre se lee junto con su dueño y no tiene vida propia se embebe
  (permisos dentro del rol, documentos e historial dentro de la cuenta de cobro).
- Lo que se consulta por sí solo es colección propia y se referencia por `_id` (ObjectId).
  Se conserva la decisión del docx: llave sustituta como identificador y llaves
  naturales como restricciones de unicidad (aquí, índices únicos).
- Los catálogos pequeños (estados, tipos de documento) pasan a enums en
  `src/gestion_documental/domain/enums.py` y se guardan como string.
- Los `CHECK` del SQL pasan a validaciones del dominio (ver tabla al final).
- Dinero en `Decimal128` (equivale a `DECIMAL(14,2)`). Las fechas sin hora (`DATE`) se guardan
  como `datetime` a medianoche UTC, porque BSON no tiene tipo fecha sin hora.

## Colecciones

| Colección | Origen SQL | Campos | Embebido / referencias |
|---|---|---|---|
| `roles` | roles, permisos, roles_permisos | nombre, descripcion, activo, permisos | `permisos`: lista de códigos, p. ej. `["cuentas.radicar", "cuentas.consultar"]` |
| `usuarios` | usuarios | nombre, apellido, correo, id_rol, cargo, contrasena_hash, activo, ultimo_acceso, intentos_fallidos, bloqueado_hasta, debe_cambiar_contrasena, fecha_registro | `id_rol` → `roles._id` |
| `contratistas` | contratistas | tipo_persona (`NATURAL`/`JURIDICA`), nombre_completo, nit_cedula, telefono, correo, direccion, activo | `tipo_persona` decide la subclase `PersonaNatural` o `PersonaJuridica` |
| `contratos` | contratos, estados_contrato | id_contratista, numero_contrato, objeto_contrato, valor_total, fecha_inicio, fecha_fin, estado, id_supervisor | `estado` como string (`ACTIVO`, `SUSPENDIDO`, ...); `id_contratista` → `contratistas._id`; `id_supervisor` → `usuarios._id` |
| `cuentas_cobro` | cuentas_cobro, estados_cuenta, historial_estado_cuenta, documentos_adjuntos, tipos_documento | id_contrato, numero_radicado, numero_cuenta, valor_cobro, concepto_pago, fecha_presentacion, estado, observaciones, id_usuario, fecha_registro, fecha_actualizacion, documentos, historial | `documentos`: lista de adjuntos (nombre_original, ruta_archivo, tipo, id_usuario, origen, fecha_carga, tipo_mime, hash_sha256, tamano_bytes); `historial`: lista de cambios (estado_anterior, estado_nuevo, id_usuario, fecha_cambio, observacion) |

El catálogo de permisos (código, descripción, módulo) deja de ser tabla: el código es el
dato que se guarda y el módulo es el prefijo del código (`cuentas.radicar` → `cuentas`).
Los 13 códigos son los del `INSERT INTO permisos` del script.

## Índices únicos (llaves naturales)

| Colección | Índice | Origen SQL |
|---|---|---|
| `roles` | `nombre` | `uq_roles_nombre` |
| `usuarios` | `correo` | `uq_usuarios_correo` |
| `contratistas` | `nit_cedula` | `uq_contratistas_nit_cedula` |
| `contratos` | `numero_contrato` | `uq_contratos_numero` |
| `cuentas_cobro` | `numero_radicado` | `uq_cuentas_cobro_radicado` |
| `cuentas_cobro` | compuesto `(id_contrato, numero_cuenta)` | `uq_cuentas_cobro_contrato_cuenta` |

Índices no únicos para las consultas frecuentes: `cuentas_cobro.estado`, `contratos.id_contratista`.

## CHECK del SQL convertidos en validación del dominio

| CHECK | Dónde se valida |
|---|---|
| `chk_contratos_valor_total` (valor_total > 0) | `ValorMonetario` en `domain/valores.py` |
| `chk_cuentas_cobro_valor` (valor_cobro > 0) | `ValorMonetario` en `domain/valores.py` |
| `chk_contratos_fechas` (fecha_fin >= fecha_inicio) | `Contrato.__post_init__` en `domain/contrato.py` |
| `chk_documentos_metadatos` (URL, o LOCAL con MIME, hash y tamaño) | `DocumentoLocal.validar()` en `domain/documentos.py` |

## Diferencias con los datos de prueba del script

- El flujo de estados del dominio es RECIBIDA → EN_REVISION → APROBADA/RECHAZADA, APROBADA → PAGADA,
  y ANULADA desde cualquier estado no final. Algunos historiales del script saltan EN_REVISION
  (p. ej. RAD-2025-0001 pasa de RECIBIDA a APROBADA). Al reconstruir una cuenta desde la BD el
  historial se carga tal cual; las reglas de transición solo se aplican a los cambios nuevos.
- Los NIT del script (`901234567`) no traen dígito de verificación; el dominio exige el formato
  `NNNNNNNNN-D`. Los datos sintéticos del proyecto usan NIT con dígito válido.
