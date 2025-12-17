# Documento 23 – Desglose diario Sprint 1

## Versión 1 (Day-by-Day Plan Sprint 1 V1)

## 1. Propósito

Este documento define el **desglose diario de Sprint 1**, cuyo objetivo es construir el **primer ciclo funcional completo del sistema**, partiendo de la base sólida creada en Sprint 0.

Sprint 1 valida que el proyecto:

* funciona de extremo a extremo
* genera valor real al tutor
* produce datos medibles y recomendaciones explicables

Sprint 1 **no busca perfección**, busca **flujo real**.

---

## 2. Objetivo global de Sprint 1

Construir y validar el ciclo mínimo:

Contenido real → estructuración → ítems → actividad del alumno
→ eventos → métricas → recomendaciones → tutor decide

Al finalizar Sprint 1, el sistema debe permitir:

* a un tutor subir contenido
* a un alumno practicar
* al sistema analizar
* al tutor decidir

---

## 3. Definición de “Done” de Sprint 1

Sprint 1 se considera completado cuando:

* existe al menos un flujo completo funcional
* se generan métricas reales
* se emite al menos una recomendación R01/R11/R21
* el tutor puede aceptarla o rechazarla
* todo queda registrado y trazable

---

## 4. Preparación previa (antes del Día 1)

Checklist:

* Sprint 0 cerrado y estable
* rama `develop` creada desde `release/sprint0`
* DB con datos seed
* usuarios de prueba:

  * 1 tutor
  * 1 alumno
* subject MAT y term T1 activos

---

## Día 1 – Ingesta de contenido académico

### Objetivo del día

Permitir al tutor subir contenido y asociarlo al contexto académico.

### Tareas

1. Implementar POST /content/uploads:

   * multipart/form-data
   * validar rol TUTOR
2. Guardar archivo en storage (local o volumen Docker).
3. Insertar registro en content_uploads.
4. Validar:

   * subject_id
   * term_id
   * topic_id (opcional)
5. Implementar GET /content/uploads (por tutor).

### Smoke check Día 1

* Tutor sube PDF pequeño → 201
* Registro visible en DB
* Archivo existe en storage

### Criterio “Día 1 completado”

* Contenido subido sin intervención manual
* Registro persistido correctamente

---

## Día 2 – Pipeline LLM mínimo (E2 + E4 simplificados)

### Objetivo del día

Transformar contenido en conocimiento estructurado e ítems básicos.

### Tareas

1. Implementar worker o servicio llm_pipeline.py.
2. Ejecutar E2 (estructura) del Doc 19:

   * summary
   * chunks básicos
3. Guardar:

   * knowledge_entries
   * knowledge_chunks
4. Ejecutar E4 (generación de ítems):

   * solo mcq y true_false
   * 6–8 ítems
5. Guardar ítems en tabla items.
6. Registrar llm_runs por etapa.

### Smoke check Día 2

* LLM produce JSON válido
* knowledge_entries + chunks creados
* items creados y visibles

### Criterio “Día 2 completado”

* Ítems generados automáticamente desde contenido real
* Sin edición manual

---

## Día 3 – Actividad del alumno (quiz funcional)

### Objetivo del día

Permitir al alumno jugar una actividad real basada en los ítems generados.

### Tareas

1. Implementar POST /activities/sessions:

   * seleccionar ítems por subject + term
2. Crear activity_sessions y activity_session_items.
3. Implementar POST /activities/sessions/{id}/responses.
4. Implementar POST /activities/sessions/{id}/end.
5. Generar learning_events por respuesta:

   * is_correct
   * duration_ms
   * attempt_number

### Smoke check Día 3

* Alumno inicia sesión
* Responde ítems
* Sesión se cierra
* Eventos insertados correctamente

### Criterio “Día 3 completado”

* Eventos reales generados por interacción del alumno

---

## Día 4 – Métricas V1 + estado de dominio

### Objetivo del día

Calcular métricas reales y estados de dominio a partir de eventos.

### Tareas

1. Implementar metric_service.py:

   * accuracy
   * first_attempt_accuracy
   * median_response_time
2. Insertar metric_aggregates.
3. Calcular mastery_states por microconcepto:

   * mastery_score
   * status (dominant / in_progress / at_risk)
4. Permitir recalcular métricas por ventana temporal.

### Smoke check Día 4

* Métricas calculadas tras sesión
* mastery_states poblados
* Valores coherentes con eventos

### Criterio “Día 4 completado”

* Métricas y dominio reflejan comportamiento real

---

## Día 5 – Motor de recomendaciones + vista tutor

### Objetivo del día

Generar recomendaciones explicables y permitir decisión del tutor.

### Tareas

1. Implementar recommendation_service.py:

   * reglas R01, R11, R21
2. Crear recommendation_instances + evidence.
3. Implementar GET /students/{id}/recommendations.
4. Implementar POST /recommendations/{id}/decision.
5. Registrar tutor_decisions y audit_logs.

### Smoke check Día 5

* Recomendación generada automáticamente
* Evidencias visibles
* Tutor acepta o rechaza

### Criterio “Día 5 completado”

* Tutor toma decisiones basadas en datos reales

---

## Día 6 – Informe automático al tutor

### Objetivo del día

Materializar el valor del sistema en un informe claro.

### Tareas

1. Implementar report_service.py.
2. Generar informe on-demand:

   * resumen ejecutivo
   * estado actual
   * recomendaciones activas
3. Guardar en tutor_reports + sections.
4. Implementar GET /reports y GET /reports/{id}.

### Smoke check Día 6

* Informe generado
* Contenido coherente con métricas y recomendaciones

### Criterio “Día 6 completado”

* Tutor puede leer y entender el estado del alumno

---

## Día 7 – Validación E2E + estabilización

### Objetivo del día

Validar el sistema completo y estabilizar.

### Tareas

1. Ejecutar E2E-01 (Doc 20).
2. Corregir bugs críticos.
3. Mejorar logs y mensajes de error.
4. Añadir tests básicos donde falten.
5. Documentar:

   * flujo completo
   * endpoints usados
   * decisiones pendientes

### Smoke check Día 7

* Flujo completo ejecutado sin errores
* Recomendaciones coherentes
* Informe generado

### Criterio “Día 7 completado”

* Sprint 1 cerrado y usable

---

## 5. Entregables finales de Sprint 1

* Flujo completo funcional
* Ítems generados automáticamente
* Métricas reales
* Recomendaciones explicables
* Informes al tutor
* Documentación actualizada

---

## 6. Puente hacia Sprint 2

Sprint 2 puede abordar:

* más tipos de actividades
* mejora del pipeline LLM (E3 y E5 completos)
* personalización avanzada
* feedback cualitativo del alumno
* mejoras UX

---

## 7. Nota final

Sprint 1 es el **momento de verdad del proyecto**.

Si este sprint funciona:

* el modelo conceptual es válido
* la arquitectura aguanta
* el proyecto tiene recorrido real

Todo lo demás es iterar y mejorar.
