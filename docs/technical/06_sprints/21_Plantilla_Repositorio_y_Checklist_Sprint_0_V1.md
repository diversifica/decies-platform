# Documento 21 – Plantilla de Repositorio y Checklist Sprint 0

## Versión 1 (Repo Template & Sprint 0 Checklist V1)

## 1. Propósito

Este documento define una plantilla práctica para iniciar el repositorio y ejecutar Sprint 0 sin fricción:

* Estructura de carpetas (monorepo)
* Convenciones de nombres
* Configuración mínima de Docker
* Checklist de tareas para cerrar Sprint 0
* Comandos de arranque y verificación

Este documento asume el stack del Documento 16:

* Backend: FastAPI + Python 3.12
* DB: PostgreSQL + Alembic
* Frontend: Next.js
* Infra: Docker + docker-compose

---

## 2. Estructura recomendada (monorepo)

```
/docs
  /00_overview
  /api
  /db
  /llm
  /testing

/backend
  /app
    /api
      /v1
        auth.py
        students.py
        subjects.py
        content.py
        activities.py
        recommendations.py
        reports.py
        grades.py
        events.py
    /core
      config.py
      security.py
      deps.py
      logging.py
    /db
      base.py
      session.py
      migrations
    /models
      user.py
      role.py
      tutor.py
      student.py
      academic.py
      content.py
      knowledge.py
      items.py
      events.py
      metrics.py
      recommendations.py
      reports.py
      grades.py
      audit.py
    /services
      auth_service.py
      student_service.py
      content_service.py
      activity_service.py
      event_service.py
      metric_service.py
      recommendation_service.py
      report_service.py
    /schemas
      auth.py
      student.py
      academic.py
      content.py
      activity.py
      events.py
      metrics.py
      recommendations.py
      reports.py
      grades.py
    /workers
      llm_pipeline.py
      metric_jobs.py
  main.py
  pyproject.toml
  README.md

/frontend
  /tutor-admin
  /student

/docker
  docker-compose.yml
  backend.Dockerfile
  frontend.Dockerfile
  initdb
    18_schema.sql
    18A_seeds.sql

/scripts
  dev_up.sh
  dev_down.sh
  db_reset.sh
  export_openapi.sh

/.env.example
/.gitignore
README.md
```

Notas:

* `docs/` debe contener los Documentos 01–21, y en adelante.
* `docker/initdb/` guarda el DDL y seeds para inicialización rápida.
* Los módulos del backend se separan en: `api`, `models`, `schemas`, `services`.

---

## 3. Convenciones técnicas (Sprint 0)

### 3.1 Nombres y estilo

* Python: snake_case
* Endpoints: kebab-case no (usar paths estándar REST)
* Migraciones Alembic: `YYYYMMDD_HHMM_<slug>.py` (si se quiere)
* Versionado:

  * API: /api/v1
  * metrics_version: V1
  * ruleset_version: V1
  * prompt_version: V1

### 3.2 Logs

* Logs estructurados (JSON) recomendados en backend.
* Nunca loggear:

  * contenido completo de PDFs
  * raw_text íntegro
  * tokens o secretos
* Sí loggear:

  * content_upload_id
  * llm_run_id
  * hashes / uris de storage
  * tiempos y estados

---

## 4. Variables de entorno (.env)

Ejemplo (no real):

```
APP_ENV=dev
APP_NAME=edu-adapt
API_PREFIX=/api/v1

POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_DB=eduadapt
POSTGRES_USER=eduadapt
POSTGRES_PASSWORD=eduadapt_password

JWT_SECRET=change_me
JWT_EXPIRES_SECONDS=3600

STORAGE_BASE_PATH=/data/storage

LLM_PROVIDER=openai|gemini|mock
LLM_MODEL_NAME=...
LLM_PROMPT_VERSION=V1
LLM_ENGINE_VERSION=V1
```

---

## 5. Docker Compose mínimo (estructura)

Archivo: /docker/docker-compose.yml

Requisitos:

* Servicio db (Postgres)
* Servicio backend (FastAPI)
* Volumen para persistencia
* Red interna

Notas:

* En Sprint 0, frontend puede omitirse o levantarse aparte.

---

## 6. Checklist Sprint 0 (tareas cerrables)

### 6.1 Repo e infraestructura

* [ ] Crear monorepo con estructura (sección 2)
* [ ] Añadir .gitignore y README raíz
* [ ] Crear .env.example
* [ ] Crear docker-compose con Postgres y backend
* [ ] Arrancar entorno local con un comando

### 6.2 Base de datos

* [ ] Aplicar DDL (Documento 18) en initdb
* [ ] Aplicar seeds (Documento 18A) en initdb
* [ ] Verificar que existen:

  * roles (3)
  * subjects (3)
  * terms (3)
  * recommendation_catalog (40)

### 6.3 Backend base

* [ ] FastAPI arranca en /health
* [ ] Configuración centralizada (core/config.py)
* [ ] Conexión a DB funcionando
* [ ] Modelo mínimo User/Role/Tutor/Student creado

### 6.4 Autenticación mínima

* [ ] Endpoint POST /auth/login (aunque sea stub en Sprint 0)
* [ ] Dependencia de autenticación (deps.py)
* [ ] Control de roles básico

### 6.5 Eventos

* [ ] Tabla learning_events operativa
* [ ] Endpoint POST /events (interno)
* [ ] Inserción real en DB
* [ ] Consulta simple por student_id

### 6.6 Documentación

* [ ] Guardar Doc 17 en /docs/api
* [ ] Guardar Doc 18 y 18A en /docs/db
* [ ] Guardar Doc 19 en /docs/llm

Criterio de cierre Sprint 0:

* Se puede crear un alumno y registrar un evento sin tocar DB manualmente.

---

## 7. Comandos recomendados (scripts)

Estos scripts son sugerencias. Puedes implementarlos en bash o powershell según entorno.

### 7.1 Arrancar entorno dev

* scripts/dev_up.sh

  * docker compose up -d
  * verificar salud de db
  * levantar backend

### 7.2 Parar entorno dev

* scripts/dev_down.sh

  * docker compose down

### 7.3 Reset completo de DB (solo dev)

* scripts/db_reset.sh

  * docker compose down -v
  * docker compose up -d
  * reaplicar initdb

### 7.4 Exportar OpenAPI

* scripts/export_openapi.sh

  * curl /openapi.json > docs/api/openapi_v1.json

---

## 8. Verificación rápida (Smoke Tests)

Al final de Sprint 0, ejecutar:

1. Verificar API viva

* GET /health → 200

2. Verificar conexión DB

* Endpoint /health/db → 200 (si se implementa)

3. Verificar seeds

* GET /subjects → 200 y contiene MAT/LEN/HIS
* GET /terms → 200 y contiene T1/T2/T3

4. Verificar alumnos y eventos (mínimo)

* POST /students → 201
* POST /events → 201/200
* GET /students/{id}/events (si existe) → devuelve eventos

---

## 9. Entregables de Sprint 0

Al finalizar Sprint 0 deberían existir:

* Repositorio funcional con estructura fija
* Entorno docker reproducible
* DB con DDL + seeds
* Backend con endpoints mínimos
* Primer registro real en learning_events
* Documentación base en /docs

---

## 10. Nota final

Este documento está pensado para que Sprint 0 sea repetible y sin decisiones abiertas.

Cuando Sprint 0 esté cerrado, el siguiente paso es:

* Sprint 1 con el primer ciclo completo (contenido → ítems → juego → eventos → métricas → recomendaciones).
