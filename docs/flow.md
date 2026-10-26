# Flujo de operación

![Flujo de operación](diagrams/flow.svg)

[Abrir SVG](diagrams/flow.svg) · [Fuente Mermaid](diagrams/flow.mmd)


La recepción valida y clasifica documentos antes de crear la salida ERP. La consulta documental utiliza las instantáneas versionadas y no modifica decisiones contables.

<details>
<summary>Versión Mermaid</summary>

```mermaid
flowchart TD
  subgraph Intake["Recepción y entrega"]
    direction TB
    Input["Texto OCR y clave de idempotencia"] --> Repeat{"¿Solicitud completada?"}
    Repeat -->|Sí| Replay["Devolver resultado persistido"]
    Repeat -->|No| Extract["Extraer por claves o LLM"]
    Extract --> Rules["Validar campos, importes y duplicados"]
    Rules --> Review{"¿Inconsistencia o extracción LLM?"}
    Review -->|Sí| Pending["Guardar pendiente de revisión"]
    Pending --> Decision{"Decisión de revisión"}
    Decision -->|Rechazar| Rejected["Rechazo y auditoría"]
    Decision -->|Aprobar| Correct{"¿Campos válidos?"}
    Correct -->|No| Pending
    Correct -->|Sí| Approved["Factura validada"]
    Review -->|No| Approved
    Approved --> Index["Actualizar fuente y versión"]
    Index --> Outbox["Una salida ERP por factura"]
    Outbox -. "integración pendiente" .-> External["Conector ERP externo"]
    External -. "recibo verificable" .-> Receipt["Confirmar y marcar exportada"]
  end
  subgraph Consultation["Consulta documental"]
    direction TB
    Question["Pregunta acotada"] --> Scope["Filtrar estados y referencia exacta"]
    Scope --> Rank["Recuperar fuentes con TF-IDF"]
    Rank --> Evidence{"¿Evidencia suficiente?"}
    Evidence -->|No| Abstain["Abstención"]
    Evidence -->|Sí| Model{"¿Solicita LLM?"}
    Model -->|No| Cite["Extractos y citas versionadas"]
    Model -->|Sí| Select["LLM selecciona fuentes recuperadas"]
    Select --> Check["Verificar identificadores de citas"]
    Check --> Selected{"¿Fuentes seleccionadas?"}
    Selected -->|Sí| Cite
    Selected -->|No| Abstain
  end
```

</details>

La aritmética se resuelve con `Decimal`. Una extracción con modelo exige revisión incluso si las sumas coinciden. Una aprobación con correcciones inválidas revierte la solicitud y conserva el documento pendiente; sólo la decisión explícita de rechazo lo marca como rechazado. Leer el outbox no acredita entrega: el conector ERP está pendiente de integración y debe aportar un recibo externo.

Cada cita incluye documento, versión, estado y extracto. Los pendientes se excluyen por defecto y los rechazados nunca se recuperan. Un modelo sólo puede seleccionar fuentes recuperadas; no puede inventar citas, corregir importes ni ejecutar acciones.

[Arquitectura](architecture.md) · [Tecnologías](technologies.md)
