# Documento 26 – Runbook E2E-02 (Sprint 2 Día 7)

## Objetivo

Ejecutar y validar el flujo E2E-02 de Sprint 2 (MATCH + fin de sesión + feedback del alumno + informe tutor).

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

## E2E-02 (tests)

Ejecuta el test E2E-02 en el contenedor backend (recomendado para evitar problemas de conexión a DB desde host):

- `docker compose -f docker-compose.dev.yml exec -T backend sh -lc "pytest -q tests/e2e/test_e2e_02_flow.py -vv"`

## Flujo E2E-02 (UI)

Nota: el pipeline actual genera principalmente ítems tipo QUIZ; para jugar MATCH en local usa el upload seed `test_upload.pdf`, que incluye un ítem MATCH.

### Tutor

1. Abre `http://localhost:3000/tutor`.
2. Inicia sesión con el tutor seed.
3. Selecciona contexto (asignatura, trimestre, alumno).
4. En tab “Contenido”: confirma que existe el upload `test_upload.pdf`.
5. En tab “Informe”: tras completar MATCH y enviar feedback (ver “Estudiante”), genera el informe y verifica que aparece una sección de feedback del alumno.

### Estudiante

1. Abre `http://localhost:3000/student`.
2. Inicia sesión con el estudiante seed.
3. Selecciona el contenido `test_upload.pdf`.
4. Inicia actividad MATCH y completa el ejercicio.
5. Finaliza la sesión y envía feedback (rating + texto).

## Endpoints clave (referencia)

- Actividades:
  - `POST /api/v1/activities/sessions` (incluye `activity_type_id=...MATCH...` y `content_upload_id`)
  - `GET /api/v1/activities/sessions/{session_id}/items`
  - `POST /api/v1/activities/sessions/{session_id}/responses`
  - `POST /api/v1/activities/sessions/{session_id}/end`
  - `POST /api/v1/activities/sessions/{session_id}/feedback`
- Informes:
  - `POST /api/v1/reports/students/{student_id}/generate?tutor_id=...&subject_id=...&term_id=...`
  - `GET /api/v1/reports/students/{student_id}/latest?tutor_id=...&subject_id=...&term_id=...`

## Problemas típicos

- “Not enough permissions”: revisa que estás logueado como el rol correcto (tutor vs student).
- “Este contenido aún no tiene ítems MATCH”: usa el upload seed `test_upload.pdf` o crea un ítem MATCH para el upload.
- “Database error reading reports”: aplica migraciones (`alembic upgrade head`) y reseedea si vienes de una versión anterior.

