# Documento 31 — Runbook E2E-06 (Sprint 6 Día 7)

## Objetivo

Ejecutar y validar el flujo E2E-06 de Sprint 6:

1) registrar una calificación real (nota) por parte del tutor
2) disparar recomendaciones `external_validation` (R31–R40) en base a esa nota
3) verificar que el informe del tutor refleja dichas recomendaciones (código + categoría)

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

## E2E-06 (tests)

Ejecuta el test E2E-06 en el contenedor `backend`:

- `docker compose -f docker-compose.dev.yml exec -T backend sh -lc "pytest -q tests/e2e/test_e2e_06_external_validation_report.py -vv"`

## Flujo E2E-06 (UI)

### Tutor: registrar nota real

1. Abre `http://localhost:3000/tutor`.
2. Inicia sesión con el tutor seed.
3. Selecciona contexto (asignatura, trimestre, alumno).
4. Tab **Notas / Calificaciones**:
   - registra una calificación baja (p.ej. `4.0` en escala `0-10`)
   - opcionalmente deja el alcance sin etiquetas (esto dispara `R33`)

### Tutor: verificar recomendaciones en informe

1. Tab **Informes**: pulsa **Generar informe**.
2. Verifica:
   - sección **Calificaciones** incluye la nota registrada
   - sección **Recomendaciones activas** incluye al menos una recomendación de categoría `external_validation` (R31–R40)
   - sección **Impacto de recomendaciones** refleja metadatos (código/categoría) cuando haya recomendaciones aceptadas con outcome

## Endpoints clave (referencia)

- Notas reales:
  - `POST /api/v1/grades`
- Informe tutor:
  - `POST /api/v1/reports/students/{student_id}/generate?tutor_id=...&subject_id=...&term_id=...&generate_recommendations=true`
- Recomendaciones:
  - `GET /api/v1/recommendations/students/{student_id}?subject_id=...&term_id=...&status_filter=pending&generate=false`

