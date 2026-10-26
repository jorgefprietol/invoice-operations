# Operación

## Consulta de facturas

Carga `data/ingest.json` con `python -m app run --input data/ingest.json --key invoice-example-001` y consulta `data/query.json` con otra clave. Ambos comandos usan `var/service.db`; la demo CLI de una sola llamada usa una base temporal y no deja datos para consultas posteriores.

Las correcciones actualizan la instantánea y el número de versión del índice dentro de la transacción de revisión. Sólo se conserva la versión actual en `invoice_sources`; las respuestas de solicitudes anteriores pueden incluir extractos históricos. Aplica la política de retención también a `requests`, auditoría y copias, no sólo al índice.

Para consultar con modelo configura `MODEL_BACKEND=ollama`, `OLLAMA_MODEL` y `OLLAMA_URL`, y envía `use_model:true`. Una respuesta inválida del proveedor revierte la consulta; nunca cambia la factura ni la salida ERP. El servicio local representa una organización: no reutilices su token o base para organizaciones que deban estar aisladas.

Antes de una carga, compruebe `/health`, el token de acceso y el volumen persistente. Conserve una clave de idempotencia por solicitud y no cambie el cuerpo durante un reintento.

Si una factura queda en `manual_review`, contraste los campos contra el documento fuente. `review_reasons` identifica campos ausentes, formato inválido o diferencia contable. Para aprobar, envíe las correcciones junto con revisor y motivo; no altere directamente las tablas.

El consumidor ERP debe leer `export`, enviar el documento con una clave externa estable y registrar `acknowledge` con el recibo obtenido. Una caída después de que el ERP acepte requiere consultar el estado remoto antes de reenviar. La lectura repetida del outbox es deliberada; no proporciona entrega exactamente una vez por sí sola.

Para medir resultados reales, registre cantidad de documentos únicos, proporción de revisión, tiempo de captura a validación y tiempo hasta confirmación del ERP. Separe errores técnicos de inconsistencias documentales. Las latencias locales del servicio no incluyen OCR, cola ni ERP.

Respalde SQLite mediante su API de backup o detenga el servicio antes de copiar la base. Restrinja acceso al archivo y establezca retención de campos y auditoría según el uso. No cargue documentos de clientes en un proveedor externo sin una política de tratamiento de datos adecuada.
