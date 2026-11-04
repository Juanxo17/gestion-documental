# Documentos en GridFS e integridad

**Qué es.** **GridFS** guarda archivos en bloques de 255 KB (`fs.files` y `fs.chunks`), sin el
límite de 16 MB por documento de MongoDB. La cuenta guarda el `_id` del archivo en `ruta_archivo`.

**Dónde está.** `domain/archivos.py` (`validar_archivo`: máximo 10 MB y tipo por los primeros
bytes, no por la extensión), `ServicioCuentas.adjuntar_archivo()` y `descargar()` en
`services/servicio_cuentas.py`, y `RepositorioArchivosGridFS` en `repositories/mongo.py`.

**Por qué el contenido y no la extensión.** Renombrar `virus.exe` a `factura.pdf` no cambia sus
primeros bytes (`MZ`); un PDF real empieza por `%PDF-`.

**Integridad.** Al subir se calcula el sha256; al descargar se recalcula leyendo GridFS por
bloques y, si no coincide, la API responde 409 en vez de entregar un archivo alterado. Si falla
guardar la cuenta, se borra el archivo ya subido para no dejar huérfanos.
