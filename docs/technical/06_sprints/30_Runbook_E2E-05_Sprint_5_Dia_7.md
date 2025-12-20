# Documento 30 — Runbook E2E-05 (Sprint 5 Día 7)

## Objetivo

Ejecutar y validar el flujo E2E-05 de Sprint 5:

1) calcular y exponer el schedule de revisión (`recommended_next_review_at`)
2) lanzar una sesión **REVIEW** (Student)
3) registrar respuestas/eventos y cerrar sesión
4) recalcular métricas
5) verificar que el Tutor ve el schedule actualizado

## Pre-requisitos

- Docker + Docker Compose funcionando.
- Servicios arriba: `db` y `backend` (y `frontend` para validación UI).
- Migraciones aplicadas y seed cargado.

## Credenciales seed (dev)

- Tutor: `tutor@decies.com` / `decies`
- Estudiante: `student@decies.com` / `decies`

## Inicialización rápida de DB (Docker)

1. Levanta entorno:
   - `make dev-up`
   - o Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\scripts\ps\dev-up.ps1`

2. Aplica migraciones:
   - Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\scripts\ps\db-migrate.ps1`
   - Alternativa directa: `docker compose -f docker-compose.dev.yml exec -T backend sh -lc "python -m alembic upgrade head"`

3. Carga seed:
   - Windows PowerShell: `powershell -ExecutionPolicy Bypass -File .\scripts\ps\db-seed.ps1`
   - Alternativa directa: `docker compose -f docker-compose.dev.yml exec -T backend sh -lc "python seed.py"`

## E2E-05 (tests)

Ejecuta el test E2E-05 en el contenedor `backend`:

- `docker compose -f docker-compose.dev.yml exec -T backend sh -lc "pytest -q tests/e2e/test_e2e_05_review_schedule.py -vv"`

## Flujo E2E-05 (UI)

### Tutor (métricas / schedule)

1. Abre `http://localhost:3000/tutor`.
2. Inicia sesión con el tutor seed.
3. Selecciona contexto (asignatura, trimestre, alumno).
4. Tab **Métricas y Dominio**:
   - Verifica el bloque de **Revisión** por microconcepto (vencidos / próximos 7 días).
   - Confirma que aparece `Siguiente Revisión` por microconcepto.

### Estudiante (REVIEW)

1. Abre `http://localhost:3000/student`.
2. Inicia sesión con el estudiante seed.
3. Pulsa **Iniciar revisión** (modo Revisión).
4. Completa una sesión (responde a varias preguntas y finaliza).

### Tutor (verificar actualización)

1. Vuelve a `http://localhost:3000/tutor`.
2. En **Métricas y Dominio**, refresca y comprueba:
   - disminuye el número de microconceptos vencidos (si se practicaron)
   - cambia `Siguiente Revisión` a una fecha futura para lo practicado

## Endpoints clave (referencia)

- Actividades (REVIEW):
  - `POST /api/v1/activities/sessions` (con `activity_type_id=...REVIEW...`, sin `content_upload_id`)
  - `GET /api/v1/activities/sessions/{session_id}/items`
  - `POST /api/v1/activities/sessions/{session_id}/responses`
  - `POST /api/v1/activities/sessions/{session_id}/end`
- Métricas:
  - `GET /api/v1/metrics/students/{student_id}/mastery?subject_id=...&term_id=...`
  - `GET /api/v1/reports/students/{student_id}/latest?tutor_id=...&subject_id=...&term_id=...` (incluye sección “Próximas revisiones”)

