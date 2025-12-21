# D-11 — Alineación del esquema de Recomendaciones con el DDL V1

## Contexto

La documentación del proyecto define un esquema de recomendaciones “V1” con:

- `recommendation_catalog` (catálogo versionable `R01..R40`, categoría, activo).
- `recommendation_instances` con contexto académico (`subject_id`, `term_id`, `topic_id`) y referencia al catálogo (`recommendation_code` FK).
- Campos de versionado/auditoría: `engine_version`, `ruleset_version`, `catalog_version`.

Referencia: `docs/technical/04_stack_tecnico/18_Esquema_Base_de_Datos_DDL_SQL_V1.md`.

## Situación actual (implementación)

En la implementación actual:

- Existe `recommendation_catalog` (seed `R01..R40`) y el backend aplica guardrail para evitar códigos inexistentes.
- `recommendation_instances` guarda:
  - `student_id`, `microconcept_id`, `rule_id`, `priority`, `status`, `title`, `description`,
  - `generated_at`, `updated_at`, `evaluation_window_days`.
- No guarda `subject_id` ni `term_id`, por lo que:
  - el filtrado por contexto depende de parámetros de API / queries ad-hoc,
  - no se puede auditar fácilmente “qué recomendación corresponde a qué asignatura/trimestre”.
- No existe FK desde `recommendation_instances` a `recommendation_catalog`.
- Versionado (`engine_version`, `ruleset_version`, `catalog_version`) no está persistido en instancias/outcomes.

## Objetivo (decisión)

Definir un plan de migración **seguro** y **faseado** para:

1) llevar `recommendation_instances` a un esquema cercano al DDL V1 (contexto + FK a catálogo),
2) mantener compatibilidad durante la transición (sin romper E2E ni datos existentes),
3) preparar la auditoría/versionado de engine/ruleset.

## Principios

- Migraciones “expand → backfill → switch → contract”.
- Mantener `develop` verde (tests + CI) en cada PR.
- Evitar “big bang”: cambios en DB, backend, frontend y tests por fases pequeñas.

## Gap principal: `term_id`

El modelo `students` actual guarda `subject_id` pero **no** guarda `term_id`.
Sin un `term_id` persistido por alumno, el backfill histórico de `term_id` en recomendaciones
no es determinista.

Por tanto:

- `subject_id` se puede backfill de forma segura desde `students.subject_id`.
- `term_id` requiere estrategia explícita (p.ej. “último term usado en sesiones” o “term actual del tutor”).

## Plan de migración propuesto (faseado)

### Fase 0 — Estado base (ya hecho)

- `recommendation_catalog` existe y está seed (R01–R40).
- Guardrail de catálogo evita instancias con códigos desconocidos.

### Fase 1 — Expand (DB)

Agregar columnas **nullable** a `recommendation_instances`:

- `subject_id` (uuid, FK a `subjects`)
- `term_id` (uuid, FK a `terms`)
- `topic_id` (uuid, FK a `topics`, opcional)
- `recommendation_code` (text, FK a `recommendation_catalog.code`)
- `engine_version` (text, default `'V1'`)
- `ruleset_version` (text, default `'V1'`)

Mantener `rule_id` durante la transición.

Índices sugeridos:

- `(student_id, status, generated_at desc)`
- `(student_id, subject_id, term_id, status, generated_at desc)`
- `(recommendation_code, status)`

### Fase 2 — Backfill (DB)

Backfill seguro:

- `subject_id`: `recommendation_instances.student_id -> students.subject_id`.
- `recommendation_code`: copiar desde `rule_id` cuando coincida con `R\\d\\d` (y exista en catálogo).

Backfill heurístico (documentar y aceptar “best effort”):

- `term_id`: derivar desde el último `ActivitySession` del alumno (por `started_at desc`), si existe.
  - Si no existe, dejar `term_id` como `NULL` temporalmente.

### Fase 3 — Switch (Backend + API)

Actualizar `RecommendationService` para escribir SIEMPRE:

- `subject_id`, `term_id` (ya se reciben como argumentos de `generate_recommendations`)
- `recommendation_code` (usar el código estable: `R01..R40`)
- `engine_version` / `ruleset_version` (por defecto `'V1'`, o constants centralizadas)

Lecturas/API:

- `GET /recommendations/students/{student_id}` debe filtrar por `subject_id` y `term_id` usando las columnas nuevas,
  evitando devolver recomendaciones de otros contextos.
- Mantener el campo `rule_id` en el payload por compatibilidad durante 1 iteración,
  pero documentar que el campo canónico pasa a ser `recommendation_code`.

### Fase 4 — Contract (DB + cleanup)

Cuando el sistema esté escribiendo el nuevo esquema y el backfill esté completado:

- Endurecer constraints:
  - `subject_id` NOT NULL
  - `recommendation_code` NOT NULL
  - `term_id` NOT NULL (solo si ya existe estrategia determinista; si no, mantener nullable y documentar)
- Deprecar `rule_id`:
  - opción A: renombrar `rule_id` → `recommendation_code` y eliminar el duplicado
  - opción B: mantener ambos y eliminar `rule_id` más adelante

## Impacto previsto (zonas a tocar)

Backend:

- Modelo SQLAlchemy: `RecommendationInstance` (nuevas columnas + FK a catálogo).
- Servicio: `backend/app/services/recommendation_service.py` (creación de instancias).
- Router: `backend/app/routers/recommendations.py` (filtros por subject/term).
- ReportService: payloads de recomendaciones en informe (pending/accepted).
- Seeds/fixtures y tests que crean instancias manualmente.

Frontend:

- Tutor/Reports: si se usa `rule_id`, migrar a `recommendation_code` cuando esté disponible.

Tests:

- Unit: `backend/tests/test_recommendations.py` (creación directa de instancias).
- E2E: flujos `tests/e2e/*` que consultan recomendaciones.

## Riesgos y mitigaciones

- **Riesgo:** backfill incorrecto de `term_id`.
  - **Mitigación:** mantener `term_id` nullable hasta tener estrategia clara;
    derivar `term_id` de sesiones recientes para la mayoría de casos.
- **Riesgo:** romper UI/consumidores por cambio de campo (`rule_id` vs `recommendation_code`).
  - **Mitigación:** compatibilidad temporal (doble campo) + deprecación documentada.
- **Riesgo:** inconsistencias en catálogo/versionado.
  - **Mitigación:** constants centralizadas y tests de guardrail.

## Checklist para PRs de implementación (referencia)

- Migración Alembic con expand/backfill sin locks largos.
- Ajustes de queries y payloads con compatibilidad.
- Tests unit + e2e actualizados.
- Runbooks (si aplica) actualizados.

## Estado

Propuesto en Sprint 7 Día 1.

