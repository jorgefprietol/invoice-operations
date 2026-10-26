# Medición del caso de facturas

El objetivo es reducir trabajo manual y tiempo de tratamiento sin trasladar errores de extracción al ERP. La consulta documental es una operación distinta del procesamiento contable y se evalúa con su propio conjunto de preguntas.

| KPI | Definición | Evidencia necesaria |
| --- | --- | --- |
| Tiempo de tratamiento | Mediana y p95 de minutos desde recepción hasta validación o revisión final | Mismos puntos de inicio/fin, marcas de tiempo, volumen y periodo antes/después |
| Tiempo de entrega | Tiempo desde validación hasta confirmación del conector ERP | Eventos de outbox y recibo externo; la demo no ejecuta un conector real |
| Productividad | Documentos correctos finalizados por hora de trabajo operativo | Horas registradas, documentos y carga de revisión humana |
| Tasa de errores | Documentos con errores confirmados / documentos auditados | Muestra contrastada contra originales; separar OCR, extracción y reglas |
| Calidad de consulta | Respuestas con fuente correcta / preguntas evaluadas | Preguntas, documentos esperados, versión citada y abstenciones revisadas |

La reducción de tiempo se calcula como `(tiempo_base - tiempo_nuevo) / tiempo_base × 100`, usando el mismo estadístico y tareas comparables. Reporta por separado los resultados de cada proceso; un intervalo entre procesos no equivale a una reducción global. Conserva número de casos, ventana de medición, criterio de exclusión y responsable de revisión. Compara complejidad, volumen y proporción de documentos retenidos para evitar atribuir al sistema diferencias de la muestra.

`python -m app metrics` mide transacciones locales únicas y latencia p50/p95 dentro del proceso. Incluye espera de base de datos y llamadas síncronas a proveedores; excluye transporte HTTP del cliente, fallos y respuestas reutilizadas. No representa tiempo humano, precisión documental ni ahorro de negocio.

Este repositorio documenta la metodología de medición y las verificaciones locales. Los ejemplos y las pruebas usan datos sintéticos; sus resultados describen únicamente la implementación y el entorno evaluados. Para una comparación operativa, registra la línea base, la muestra y el periodo de medición con datos autorizados y anonimizados.
