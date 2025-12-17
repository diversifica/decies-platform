# Sprint 1 – Issues (local)

Este archivo sirve como backlog local (formato tipo issue) para cerrar Sprint 1 siguiendo `CONTRIBUTING.md`.

## Issue S1-D6-A – Backend: Informe automático al tutor

**Objetivo:** generar un informe on-demand con resumen ejecutivo, estado actual (métricas/dominio) y recomendaciones activas; persistirlo y hacerlo consultable por API.

**Criterios de aceptación**
- Existe endpoint `POST /api/v1/reports/students/{student_id}/generate` que genera y persiste un informe.
- Existe endpoint `GET /api/v1/reports/students/{student_id}/latest` que devuelve el último informe para (tutor, subject, term).
- El informe incluye secciones mínimas: `executive_summary`, `mastery`, `recommendations`.
- No usa LLM (determinista) y funciona con datos seed.

**Tareas**
- Añadir modelos `TutorReport` y `TutorReportSection` + migración Alembic.
- Añadir schemas Pydantic de reports.
- Añadir `ReportService` que arma secciones desde métricas/mastery/recomendaciones.
- Añadir router `reports` e incluirlo en `app.main`.

## Issue S1-D6-B – Frontend: Vista de informes en panel del tutor

**Objetivo:** permitir generar y visualizar el informe desde el front.

**Criterios de aceptación**
- Nuevo tab “Informe” en `/tutor`.
- Botón “Generar informe” que llama al endpoint de generación.
- Render de secciones del informe (al menos resumen + recomendaciones).

**Tareas**
- Crear componente `TutorReportPanel`.
- Integrarlo como tab en `frontend/src/app/tutor/page.tsx`.

## Issue S1-D6-C – (Opcional) Auth/UI: eliminar IDs hardcodeados

**Objetivo:** preparar el siguiente paso para que el usuario real (tutor) no dependa de pegar UUIDs.

**Criterios de aceptación**
- Endpoint `GET /api/v1/auth/me` implementado.
- Front guarda token y deriva `tutor_id`/`student_id` desde sesión o API.

