# Invoice Operations

Servicio de recepción y control de facturas. Convierte texto OCR en campos estructurados, valida importes con aritmética decimal y retiene inconsistencias para revisión antes de generar una salida hacia ERP.

El flujo separa extracción, decisión contable y entrega. Una respuesta del extractor nunca equivale a una aprobación.

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

La clave de negocio es proveedor más número de factura. Una repetición idéntica no crea otra salida. Un documento con esa clave y contenido diferente se rechaza para investigación. Las notas de crédito requieren otro contrato: esta versión admite importes positivos o cero, sin compensaciones fiscales implícitas.

El contrato de dos decimales admite USD, EUR, GBP, CAD, AUD, CHF, MXN, BRL, COP, PEN y ARS. Otras monedas pasan a revisión y no pueden aprobarse dentro de este contrato. El código no sustituye validaciones fiscales por país.

Ejemplo de corrección:

```json
{"action":"review","document_id":"ID_RECIBIDO","decision":"approve","reviewer":"finance-01","reason":"Contraste con documento fuente","corrections":{"total":"143.75"}}
```

## Evidencia y operación

Las pruebas cubren duplicados, importes con precisión inválida, OCR contradictorio, revisión y confirmación de entrega. `/api/metrics` expone latencia y transacciones observadas en esta instancia. La tasa de revisión se obtiene dividiendo facturas retenidas entre recibidas; el tiempo por documento requiere registrar además el inicio de captura y la recepción del ERP. No se atribuye ahorro operativo a los datos de demostración.

El outbox permite desarrollar un conector ERP con reintentos y recibos estables. Ese conector, el motor OCR, la identidad corporativa y la validación tributaria por país quedan fuera del despliegue local. Consulte [arquitectura](docs/architecture.md), [decisiones](docs/decisions.md), [operación](docs/operations.md) y [referencias](docs/references.md).
