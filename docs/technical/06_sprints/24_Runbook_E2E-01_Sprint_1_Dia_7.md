# Documento 24 – Runbook E2E-01 (Sprint 1 Día 7)

## Objetivo

Ejecutar manualmente el flujo E2E-01 de Sprint 1 (contenido → ítems → sesión → eventos → métricas → recomendaciones → decisión tutor → informe).

## Pre-requisitos

- Docker + Docker Compose funcionando.
- Servicios arriba: `db` y `backend` (y opcionalmente `frontend`).
- Migraciones aplicadas y seed cargado.

## Credenciales seed (dev)

- Tutor: `tutor@decies.com` / `decies`
- Estudiante: `student@decies.com` / `decies`

Si no puedes iniciar sesión, normalmente es porque tu base de datos no ha sido reseedeada tras actualizar el repo.

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

## Flujo E2E-01 (UI)

### Tutor

1. Abre `http://localhost:3000/tutor`.
2. Inicia sesión con el tutor.
3. Selecciona contexto (asignatura, trimestre, alumno).
4. En tab “Contenido”: sube un PDF.
5. En la lista de uploads, pulsa “Procesar” para generar ítems.
6. En tab “Métricas y Dominio”: tras sesiones del alumno, verifica que se muestran métricas y dominio por microconcepto.
7. En tab “Recomendaciones”: verifica que aparecen reglas (R01/R11/R21 según datos) y registra una decisión.
8. En tab “Informe”: genera el informe y verifica que muestra secciones (resumen, dominio, recomendaciones).

### Estudiante

1. Abre `http://localhost:3000/student`.
2. Inicia sesión con el estudiante.
3. Selecciona un upload y comienza actividad.
4. Finaliza la sesión para disparar recálculo de métricas.

## Endpoints clave (referencia)

- Auth:
  - `POST /api/v1/login/access-token`
  - `GET /api/v1/auth/me`
- Catálogo (contexto):
  - `GET /api/v1/catalog/subjects?mine=true`
  - `GET /api/v1/catalog/terms?active=true`
  - `GET /api/v1/catalog/students?mine=true&subject_id=...`
- Contenido:
  - `POST /api/v1/content/uploads`
  - `POST /api/v1/content/uploads/{upload_id}/process`
  - `GET /api/v1/content/uploads/{upload_id}/items`
- Actividades:
  - `POST /api/v1/activities/sessions`
  - `POST /api/v1/activities/sessions/{session_id}/responses`
  - `POST /api/v1/activities/sessions/{session_id}/end`
- Métricas:
  - `GET /api/v1/metrics/students/{student_id}/metrics?subject_id=...&term_id=...`
  - `GET /api/v1/metrics/students/{student_id}/mastery?subject_id=...&term_id=...`
- Recomendaciones:
  - `GET /api/v1/recommendations/students/{student_id}?subject_id=...&term_id=...`
  - `POST /api/v1/recommendations/{recommendation_id}/decision`
- Informes:
  - `POST /api/v1/reports/students/{student_id}/generate?tutor_id=...&subject_id=...&term_id=...`
  - `GET /api/v1/reports/students/{student_id}/latest?tutor_id=...&subject_id=...&term_id=...`
  - `GET /api/v1/reports?tutor_id=...`
  - `GET /api/v1/reports/{report_id}?tutor_id=...`

## Notas

- El pipeline LLM usa mocks en CI; en local necesitas `OPENAI_API_KEY` si quieres procesamiento real.
- Existe un endpoint dev `POST /api/v1/microconcepts/bootstrap` para alinear dominio si tu dataset tiene sesiones pero no microconceptos por asignatura/trimestre.
