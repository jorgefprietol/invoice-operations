# Invoice Operations

Servicio de recepción, consulta y control de facturas. Convierte texto OCR en campos estructurados, valida importes con aritmética decimal y retiene inconsistencias para revisión antes de generar una salida hacia ERP. La consulta documental recupera registros normalizados con citas y versiones; puede incorporar un LLM mediante Ollama.

## Contexto y confidencialidad

Este caso de uso forma parte de mi experiencia en soluciones implementadas en producción durante trabajos de consultoría. La versión pública es una implementación independiente con datos sintéticos que permite revisar la arquitectura, los flujos y los controles. Por confidencialidad, no se incluyen la identidad del cliente, su código ni sus registros operativos.

El flujo separa extracción, decisión contable y entrega. Una respuesta del extractor nunca equivale a una aprobación.

[Diseño de arquitectura](docs/architecture.md) · [Flujos diagramados](docs/flow.md) · [Tecnologías utilizadas](docs/technologies.md)

## Ejecutar

Requiere Python 3.10 o posterior. La demo funciona sin dependencias externas, con una base temporal y datos sintéticos.

```powershell
python -m app demo
python -m unittest discover -s tests -v
$env:SERVICE_TOKEN = 'un-token-local-de-al-menos-24-caracteres'
python -m app serve
```

Abra `http://127.0.0.1:8080` para ejecutar solicitudes y consultar métricas. La API acepta `POST /api/run` con `Authorization: Bearer <SERVICE_TOKEN>` y un `Idempotency-Key` nuevo por operación. Reutilizar la misma clave con el mismo cuerpo devuelve la respuesta original; cambiar el cuerpo produce un conflicto.

## Entrada

```json
{
  "action": "ingest",
  "ocr_text": "supplier_tax_id: DEMO-179001\ndocument_number: F-42\nissue_date: 2026-10-26\ncurrency: USD\nsubtotal: 125.00\ntax: 18.75\ntotal: 143.75"
}
```

El modo local reconoce claves por línea; admite `ruc`, `factura`, `fecha`, `moneda` e `iva`. Espera texto ya extraído: no ejecuta un motor OCR sobre imágenes o PDF. Los importes aceptan punto o coma decimal, sin separadores de miles, y se conservan con dos decimales.

Para documentos de formato libre, configure el proveedor descrito en `.env.example` y envíe `"use_model": true`. La extracción estructurada pasa por las mismas validaciones que el modo local y siempre requiere revisión humana contra el documento fuente antes de entrar al outbox: la coherencia aritmética no demuestra fidelidad de extracción. El modelo no modifica el ERP ni decide aprobaciones.

## Operaciones

| Acción | Comportamiento |
| --- | --- |
| `ingest` | Extrae, comprueba campos y registra la factura. |
| `review` | Aprueba con correcciones válidas o rechaza una factura pendiente; exige revisor y motivo. |
| `export` | Lee hasta cien registros pendientes del outbox. No los marca como entregados. |
| `acknowledge` | Registra el recibo de un conector externo y cierra la entrega. |
| `query` | Recupera facturas con fuentes versionadas y abstención ante evidencia insuficiente. |

La clave de negocio es proveedor más número de factura. Una repetición idéntica no crea otra salida. Un documento con esa clave y contenido diferente se rechaza para investigación. Las notas de crédito requieren otro contrato: esta versión admite importes positivos o cero, sin compensaciones fiscales implícitas.

El contrato de dos decimales admite USD, EUR, GBP, CAD, AUD, CHF, MXN, BRL, COP, PEN y ARS. Otras monedas pasan a revisión y no pueden aprobarse dentro de este contrato. El código no sustituye validaciones fiscales por país.

Ejemplo de corrección:

```json
{"action":"review","document_id":"ID_RECIBIDO","decision":"approve","reviewer":"finance-01","reason":"Contraste con documento fuente","corrections":{"total":"143.75"}}
```

## Consulta documental y RAG

Para probar recepción y consulta sobre la misma base persistente:

```powershell
python -m app run --input data/ingest.json --key invoice-example-001
python -m app run --input data/query.json --key invoice-query-001
```

La operación de consulta acepta:

```json
{"action":"query","question":"Total factura F-2026-0042","limit":3,"use_model":false}
```

El índice usa TF-IDF sobre los campos actuales, no sobre instrucciones del OCR. Devuelve extractos exactos con identificador, versión y estado. Una corrección actualiza el índice en la misma transacción que la factura. Las fuentes validadas o exportadas están disponibles por defecto; `include_pending:true` añade pendientes claramente identificados. Los documentos rechazados se excluyen siempre.

Con `MODEL_BACKEND=ollama` y `use_model:true`, el recorrido RAG envía al modelo la pregunta y las fuentes recuperadas para seleccionar las relevantes. La API verifica sus identificadores y conserva los importes de los extractos; una cita inventada se rechaza. La selección vacía o una búsqueda sin coincidencias producen abstención. La consulta no aprueba facturas ni modifica el outbox.

La base corresponde a una organización. El token compartido da acceso a ese corpus; el aislamiento entre organizaciones requiere bases y credenciales independientes o una ampliación de identidad y partición.

## Evidencia y operación

Las pruebas cubren duplicados, importes con precisión inválida, OCR contradictorio, revisión y confirmación de entrega. `/api/metrics` expone latencia y transacciones observadas en esta instancia. La tasa de revisión se obtiene dividiendo facturas retenidas entre recibidas; el tiempo por documento requiere registrar además el inicio de captura y la recepción del ERP. No se atribuye ahorro operativo a los datos de demostración.

El outbox permite desarrollar un conector ERP con reintentos y recibos estables. Ese conector, el motor OCR, la identidad corporativa y la validación tributaria por país quedan fuera del despliegue local. Consulte [arquitectura](docs/architecture.md), [flujo](docs/flow.md), [tecnologías](docs/technologies.md), [decisiones](docs/decisions.md), [operación](docs/operations.md) y [referencias](docs/references.md).
