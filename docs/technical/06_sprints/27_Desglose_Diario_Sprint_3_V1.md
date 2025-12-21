# Documento 27 – Desglose diario Sprint 3

## Versión 1 (Day-by-Day Plan Sprint 3 V1)

## 1. Propósito

Sprint 3 extiende el valor educativo y el control tutor sobre el contenido:

- Taxonomía de microconceptos gestionable (CRUD + prerequisitos).
- Recomendaciones que aprovechan prerequisitos (R05) y mejoran la selección adaptativa.
- Más variedad de actividades e ítems (p. ej. CLOZE y/o generación de MATCH desde contenido).
- Revisión/activación de ítems por tutor para evitar “ruido” en el aprendizaje.
- Validación end-to-end adicional y estabilización.

---

## 2. Objetivo global de Sprint 3

Conseguir un flujo donde el tutor pueda:

1) definir y mantener microconceptos (y prerequisitos),
2) practicar con el alumno usando actividades variadas,
3) recibir recomendaciones que incluyan prerequisitos cuando haya fallos base,
4) controlar qué ítems quedan activos y se sirven al alumno.

---

## 3. Definición de “Done” de Sprint 3

Sprint 3 se considera completado cuando:

- El tutor puede crear/editar/desactivar microconceptos en su asignatura y trimestre.
- Existe gestión de prerequisitos (microconcept_prerequisites) y se usa en al menos 1 recomendación (R05).
- La selección adaptativa tiene en cuenta prerequisitos (cuando aplica) y mantiene diversidad.
- Existe al menos 1 nueva actividad adicional (p. ej. CLOZE) o generación automática de ítems MATCH desde contenido.
- Se ejecuta un E2E adicional (E2E-03) y CI permanece verde.

---

## Día 1 – CRUD de microconceptos (tutor)

### Objetivo del día

Permitir que el tutor gestione microconceptos de su materia (sin depender de seed).

### Tareas

1. Endpoints: crear/editar/desactivar microconceptos con RBAC (tutor solo en sus subjects).
2. UI tutor: listado + alta/edición rápida de microconceptos por asignatura/trimestre.
3. Ajustes de catálogo para refrescar microconceptos tras cambios.
4. Tests API + smoke UI.

### Smoke check Día 1

- El tutor crea/edita microconceptos y el alumno puede practicar sobre ellos (vía ítems existentes).

---

## Día 2 – Prerequisitos (modelo + endpoints)

### Objetivo del día

Gestionar relaciones de prerequisitos entre microconceptos.

### Tareas

1. Endpoints para crear/listar/eliminar prerequisitos (microconcept_prerequisites).
2. Validaciones: evitar ciclos obvios, duplicados y relaciones cross-subject/term.
3. UI tutor: editor sencillo de prerequisitos (selección múltiple).
4. Tests de integridad.

### Smoke check Día 2

- Se guardan prerequisitos y se reflejan al consultar microconceptos.

---

## Día 3 – Recomendación R05 (prerequisitos)

### Objetivo del día

Incluir prerequisitos cuando el alumno falla repetidamente un microconcepto base.

### Tareas

1. Implementar regla R05 (“Reforzar prerequisitos”) en RecommendationService.
2. Evidencia: microconcept en riesgo + prerequisitos con bajo dominio/alta tasa de error.
3. Exponer en UI tutor con explicación y acción (decisión del tutor).
4. Tests deterministas.

### Smoke check Día 3

- Aparece una recomendación R05 en un dataset con prerequisitos y bajo dominio.

---

## Día 4 – Selección adaptativa V2 (incluye prerequisitos)

### Objetivo del día

Mejorar la creación de sesiones para mezclar microconceptos en riesgo con prerequisitos relevantes.

### Tareas

1. Extender `POST /activities/sessions` para:
   - priorizar `at_risk`,
   - incluir prerequisitos cuando hay señales de fallo base,
   - mantener diversidad y límites por microconcepto.
2. Tests de selección (dataset controlado).
3. Ajustar métricas si hace falta por la nueva mezcla.

### Smoke check Día 4

- En un caso con prerequisitos, una sesión incluye ítems del prerequisito cuando procede.

---

## Día 5 – Nueva actividad (CLOZE) o generación de MATCH

### Objetivo del día

Aumentar variedad de práctica real.

### Opciones (elegir 1 para Sprint 3 V1)

**Opción A (CLOZE):**
1. Soportar ítems CLOZE (texto con huecos + respuestas).
2. UI alumno para CLOZE.
3. Persistir eventos coherentes y recalcular métricas.

**Opción B (MATCH auto desde contenido):**
1. Extender pipeline para generar un pequeño set de ítems MATCH por upload (con validación).
2. Asegurar que el alumno puede jugar MATCH con ítems generados (no solo seed).

### Smoke check Día 5

- Existe una nueva modalidad jugable end-to-end con eventos y métricas.

---

## Día 6 – Revisión/activación de ítems por tutor

### Objetivo del día

Evitar servir ítems incorrectos/ruidosos al alumno.

### Tareas

1. UI tutor: tabla de ítems por upload con acciones (activar/desactivar).
2. Backend: endpoints para togglear `is_active` y filtrar por `is_active=true` al servir sesiones.
3. Tests básicos.

### Smoke check Día 6

- Desactivar un ítem evita que salga en nuevas sesiones.

---

## Día 7 – Validación E2E + estabilización Sprint 3

### Objetivo del día

Validación completa y estabilización para el siguiente sprint.

### Tareas

1. Definir y ejecutar E2E-03:
   - incluye prerequisitos (R05) y la nueva actividad (CLOZE o MATCH generado).
2. Corregir bugs críticos.
3. Aumentar tests donde falten.
4. Documentar endpoints y decisiones pendientes.

### Smoke check Día 7

- E2E-01, E2E-02 y E2E-03 ejecutan sin intervención manual y CI verde.

---

## 4. Entregables finales de Sprint 3

- CRUD microconceptos + prerequisitos (tutor).
- Recomendación R05 y selección adaptativa con prerequisitos.
- Nueva modalidad de práctica (CLOZE o MATCH generado).
- Revisión de ítems por tutor.
- E2E-03 + documentación.

