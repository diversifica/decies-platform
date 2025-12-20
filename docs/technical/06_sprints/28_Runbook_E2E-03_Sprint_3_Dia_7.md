# Documento 28 – Runbook E2E-03 (Sprint 3 Día 7)

## Objetivo

Ejecutar y validar el flujo E2E-03 de Sprint 3 (prerequisitos + recomendación R05 + actividad CLOZE).

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

## E2E-03 (tests)

Ejecuta el test E2E-03 en el contenedor backend:

- `docker compose -f docker-compose.dev.yml exec -T backend sh -lc "pytest -q tests/e2e/test_e2e_03_prereq_r05_cloze.py -vv"`

## Flujo E2E-03 (UI)

### Tutor (prerequisitos + recomendaciones)

1. Abre `http://localhost:3000/tutor`.
2. Inicia sesión con el tutor seed.
3. Selecciona contexto (asignatura, trimestre, alumno).
4. Tab “Microconceptos”: abre “Prerequisitos” y crea al menos una relación (A depende de B).
5. Tab “Recomendaciones”: tras una sesión donde el alumno falle A, verifica que aparece una recomendación R05 para practicar B.

### Estudiante (CLOZE)

1. Abre `http://localhost:3000/student`.
2. Inicia sesión con el estudiante seed.
3. Selecciona el contenido `test_upload.pdf`.
4. Inicia actividad **Cloze** y completa el ejercicio.

## Endpoints clave (referencia)

- Microconceptos (prerequisitos):
  - `GET /api/v1/microconcepts/{id}/prerequisites`
  - `POST /api/v1/microconcepts/{id}/prerequisites`
  - `DELETE /api/v1/microconcepts/{id}/prerequisites/{prereq_id}`
- Actividades (CLOZE):
  - `POST /api/v1/activities/sessions` (con `activity_type_id=...CLOZE...`)
  - `GET /api/v1/activities/sessions/{session_id}/items`
  - `POST /api/v1/activities/sessions/{session_id}/responses`
  - `POST /api/v1/activities/sessions/{session_id}/end`
- Recomendaciones:
  - `GET /api/v1/recommendations/students/{student_id}?subject_id=...&term_id=...`

