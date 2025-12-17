# Documento 25 – Desglose diario Sprint 2

## Versión 1 (Day-by-Day Plan Sprint 2 V1)

## 1. Propósito

Sprint 2 consolida el sistema tras Sprint 1 y extiende el valor con:

- Pipeline LLM más robusto (E3 + E5).
- Más tipos de actividad.
- Personalización en selección de ítems.
- Feedback cualitativo del alumno integrado en el informe.
- Estabilización y validación end-to-end.

---

## 2. Objetivo global de Sprint 2

Completar y estabilizar el flujo:

Contenido → E2/E3/E4/E5 → ítems trazables → actividades (más de un tipo) → eventos
→ métricas/dominio → recomendaciones → tutor decide → informe (incluye feedback).

---

## 3. Definición de “Done” de Sprint 2

Sprint 2 se considera completado cuando:

- Pipeline LLM incluye E3 (mapeo) y E5 (validación) con trazabilidad mínima.
- Existe al menos 1 actividad adicional a QUIZ (MATCH mínimo).
- La creación de sesiones prioriza microconceptos según dominio (adaptativo V1).
- El alumno puede dejar feedback post-sesión y el tutor lo ve en informe.
- Se ejecuta un E2E adicional (E2E-02) y CI permanece verde.

---

## Día 1 – Endurecer contexto + RBAC

### Objetivo del día

Eliminar dependencias de UUIDs pegados y asegurar control de acceso coherente.

### Tareas

1. Alinear RBAC en endpoints críticos (tutor vs student).
2. Derivar contexto desde “usuario actual” siempre que aplique:
   - quitar `tutor_id` en query/body donde sea redundante.
3. Homogeneizar errores 401/403 y mensajes.

### Smoke check Día 1

- Tutor solo ve sus asignaturas/alumnos/uploads.
- Student solo ve/crea sesiones de sí mismo.

---

## Día 2 – Pipeline LLM: E3 (mapeo a microconceptos)

### Objetivo del día

Implementar E3 según Documento 19 para mapear chunks/ítems a microconceptos existentes.

### Tareas

1. Construir entrada E3 (`microconcept_catalog`, `chunks_from_E2`) y ejecutar prompt E3.
2. Persistir resultado de mapeo:
   - `knowledge_chunks.microconcept_id` (y campos mínimos si faltan).
3. Ajustar asignación de `Item.microconcept_id` para usar E3 (con fallback controlado).
4. Tests con mocks (CI determinista).

### Smoke check Día 2

- Procesar un upload produce ítems con `microconcept_id` no trivial (no todo “General”).

---

## Día 3 – Pipeline LLM: E5 (validación de ítems)

### Objetivo del día

Filtrar/corregir ítems ambiguos antes de persistirlos como activos.

### Tareas

1. Implementar E5 (validate) tras E4.
2. Conservar solo ítems `ok` o `fix` (descartar `drop`) y registrar el motivo.
3. Añadir trazabilidad mínima:
   - `source_chunk_index`, `validation_status`, `validation_reason` (según modelo/DDL real).
4. Tests unit/integration con mocks.

### Smoke check Día 3

- El pipeline descarta ítems ambiguos (E5) y deja un set coherente.

---

## Día 4 – Nuevos tipos de actividad (MATCH mínimo)

### Objetivo del día

Añadir un juego adicional real (MATCH) end-to-end.

### Tareas

1. Extender modelo/DTOs para soportar ítems tipo MATCH (pares).
2. Implementar endpoints de sesión/respuestas para MATCH (reutilizando `learning_events`).
3. Implementar UI mínima en frontend (student) para jugar MATCH.
4. Asegurar que métricas se recalculan con eventos de MATCH.

### Smoke check Día 4

- Un alumno completa MATCH y quedan `learning_events` coherentes.

---

## Día 5 – Personalización avanzada (selección adaptativa V1)

### Objetivo del día

Mejorar selección de ítems al crear sesiones: priorizar “en riesgo” y diversidad.

### Tareas

1. Algoritmo V1 en `POST /activities/sessions`:
   - priorizar microconceptos `at_risk`,
   - mezclar con `in_progress` para evitar sesgo,
   - límite por microconcepto para diversidad.
2. Ajustar recomendación/métricas si se requieren cambios por nuevas actividades.
3. Tests de selección (deterministas) con dataset seed.

### Smoke check Día 5

- Con estados de dominio, una sesión tiende a sacar ítems de microconceptos “en riesgo”.

---

## Día 6 – Feedback cualitativo del alumno + informe

### Objetivo del día

Capturar feedback post-sesión y mostrarlo al tutor, incluido en el informe.

### Tareas

1. Modelo + endpoint `POST /activities/sessions/{id}/feedback`.
2. Mostrar feedback en vista tutor (y/o detalle de sesión).
3. Incluir feedback relevante en el informe generado (ReportService).
4. Tests básicos.

### Smoke check Día 6

- El tutor ve feedback del alumno y aparece en el informe generado.

---

## Día 7 – Validación E2E + estabilización Sprint 2

### Objetivo del día

Ejecutar validación completa y estabilizar el sistema para iterar en Sprint 3.

### Tareas

1. Definir y ejecutar E2E-02:
   - incluye MATCH y feedback además del flujo base.
2. Corregir bugs críticos.
3. Aumentar tests donde falten.
4. Documentar endpoints y decisiones pendientes.

### Smoke check Día 7

- E2E-01 y E2E-02 ejecutan sin intervención manual y CI verde.

---

## 4. Entregables finales de Sprint 2

- Pipeline LLM con E3/E5 (tolerante y trazable).
- MATCH como segunda actividad.
- Selección adaptativa V1.
- Feedback cualitativo integrado en informe.
- Documentación + tests de regresión básicos.

