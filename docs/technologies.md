# Tecnologías utilizadas

| Tecnología | Uso concreto | Estado |
| --- | --- | --- |
| Python 3.10+ | Servicio, reglas de negocio y CLI con biblioteca estándar. | Implementado localmente. |
| SQLite | Facturas, índice documental, versiones, outbox, auditoría e idempotencia. | Implementado localmente. |
| `decimal.Decimal` | Comprobar importes sin redondeo binario. | Implementado localmente. |
| TF-IDF y similitud coseno | Recuperar registros normalizados y producir citas. | Implementado sin base vectorial externa. |
| Ollama y LLM | Extracción estructurada y selección de fuentes dentro del recorrido RAG. | Adaptador opcional; requiere modelo instalado. |
| HTTP REST y JSON | Integrar captura, consulta, revisión y confirmación mediante una API. | Implementado con token y límites de entrada. |
| n8n | Encadenar webhook autenticado y API de negocio. | Workflow incluido; importar y configurar credenciales. |
| Docker y Compose | Empaquetar servicio y orquestador opcional. | Definiciones incluidas; validar en el entorno destino. |
| GitHub Actions y `unittest` | Verificar reglas, recuperación, transacciones y contrato HTTP. | Automatización incluida. |
| Mermaid | Mantener arquitectura y flujos junto al código. | Diagramas editables en Markdown. |

El proyecto recibe texto de OCR; no incluye un motor de reconocimiento de imágenes. La salida ERP es un contrato de entrega pendiente y confirmación, no una conexión a un ERP particular. No utiliza LangChain, embeddings ni una base vectorial: el motor de recuperación actual es léxico.

[Arquitectura](architecture.md) · [Flujo](flow.md) · [Configuración de integraciones](integrations.md)
