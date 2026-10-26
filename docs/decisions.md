# Decisiones de diseño

1. **Importes decimales.** No se utilizan números flotantes para validar subtotal, impuesto y total. Una precisión mayor de dos decimales se retiene para revisión, sin redondeo silencioso.
2. **Doble idempotencia.** La capa HTTP protege el reintento técnico; proveedor y número protegen contra cargas repetidas con otra clave HTTP. Una colisión de contenido no se resuelve sobrescribiendo.
3. **Outbox explícito.** La transacción local no puede ser atómica con un ERP remoto. El estado pendiente más un recibo externo permite reintentar y distinguir preparación de entrega.
4. **Aprobación controlada.** El extractor propone campos; las reglas comprueban consistencia. Las extracciones con modelo siempre requieren revisión del documento fuente antes del outbox. Una revisión necesita motivo y datos válidos. El campo `reviewer` es una referencia de auditoría; un gateway corporativo debe asociarlo a una identidad autenticada y autorizar la operación.
5. **Formato acotado.** La demo procesa texto estructurado y no pretende sustituir un OCR ni un validador tributario. La opción de modelo mantiene el contrato de salida y la validación del dominio.
