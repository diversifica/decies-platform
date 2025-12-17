# Documento 22 – Desglose diario Sprint 0

## Versión 1 (Day-by-Day Plan Sprint 0 V1)

## 1. Propósito

Este documento convierte el Sprint 0 (Documento 13 y 21) en un plan diario ejecutable, con:

* Orden exacto de construcción
* Dependencias entre tareas
* Validaciones diarias (smoke checks)
* Criterio objetivo de “día completado”

Asume sprint de 5 días laborables. Si tu sprint es de 2 semanas, se puede ampliar manteniendo el orden.

---

## 2. Definición de “Done” por día

Un día se considera completado cuando:

* Se ha implementado lo previsto.
* Se ha pasado el smoke check del día.
* Se han actualizado notas breves en /docs (log de cambios).

---

## 3. Preparación previa (antes del Día 1)

Checklist:

* Tener instalado Docker Desktop.
* Tener Git configurado.
* Tener Python 3.12 disponible (si no se dockeriza todo).
* Tener un editor (VS Code).

Resultado esperado:

* Puedes crear repo y ejecutar comandos base.

---

## Día 1 – Monorepo + Docker + DB inicial

### Objetivo del día

Tener el repo con estructura base y una base de datos levantada con Docker.

### Tareas

1. Crear repositorio git (monorepo) y estructura de carpetas (Doc 21).
2. Añadir .gitignore, README raíz y .env.example.
3. Crear docker-compose con:

   * postgres
   * volumen persistente
4. Preparar initdb:

   * docker/initdb/18_schema.sql (DDL)
   * docker/initdb/18A_seeds.sql (seeds)
5. Verificar arranque Postgres y aplicación automática de initdb (si configuras initdb).

### Smoke check Día 1

* docker compose up -d
* Se crea la DB sin errores.
* Verificar seeds (consultas):

Esperado:

* roles = 3
* subjects >= 3
* terms = 3
* recommendation_catalog = 40

### Criterio “Día 1 completado”

* Repo estructurado y commiteado.
* DB arriba y seed aplicada.
* Evidencia: screenshot o log de consultas en /docs/testing/sprint0_day1.md

---

## Día 2 – Backend FastAPI mínimo + Health + DB Session

### Objetivo del día

Backend arrancando y conectando a la DB correctamente.

### Tareas

1. Crear proyecto backend con FastAPI.
2. Implementar /health (200).
3. Implementar /health/db (200 si conecta).
4. Crear módulo core/config.py para leer variables de entorno.
5. Crear db/session.py y conexión SQLAlchemy.
6. Verificar que el backend corre dentro de Docker o local (elige una vía y documenta).

### Smoke check Día 2

* GET /health → 200
* GET /health/db → 200

### Criterio “Día 2 completado”

* Backend en ejecución + DB OK.
* Documentar cómo arrancar backend en README backend.

---

## Día 3 – Modelos base + migraciones (Alembic) + roles seed

### Objetivo del día

Tener el sistema listo para evolución controlada del esquema.

### Tareas

1. Inicializar Alembic en /backend/app/db/migrations
2. Configurar Alembic para conectar a Postgres.
3. Crear modelos mínimos:

   * users
   * roles
   * user_roles
   * tutors
   * students
   * student_tutor_links
4. Decidir estrategia de migraciones:

   * Opción A: DDL base en initdb + Alembic para cambios posteriores.
   * Opción B: Todo por Alembic desde cero.

Recomendación V1:

* Mantener DDL base para levantar rápido en dev.
* Mantener Alembic para cambios incrementales.

5. Añadir seed mínimo de roles (si no se usa initdb).

### Smoke check Día 3

* Ejecutar migración (si aplica) sin errores.
* Insertar un usuario y rol (manualmente o por script) y comprobar.

### Criterio “Día 3 completado”

* Alembic configurado y funcionando.
* Modelos base listos.
* Se puede crear un usuario en DB sin inconsistencias.

---

## Día 4 – Autenticación mínima + RBAC

### Objetivo del día

Autenticación base operativa y control de roles aplicado en endpoints.

### Tareas

1. Implementar POST /auth/login (mínimo viable).

   * Validación credenciales
   * Emisión JWT
2. Implementar GET /auth/me.
3. Implementar dependencias:

   * get_current_user
   * require_role(TUTOR/ADMIN/PLAYER)
4. Crear endpoint protegido de prueba:

   * GET /admin/ping (solo ADMIN)
5. Crear usuario admin seed (solo en dev).
6. Documentar flujo de login (curl examples).

### Smoke check Día 4

* Login correcto → token
* /auth/me → 200
* /admin/ping con token tutor → 403
* /admin/ping con token admin → 200

### Criterio “Día 4 completado”

* JWT funcionando.
* RBAC validado con pruebas simples.

---

## Día 5 – Endpoints base de alumnos + Eventos (append-only)

### Objetivo del día

Cerrar Sprint 0 con:

* creación de alumnos por tutor
* registro real de eventos en learning_events

### Tareas

1. Implementar POST /students (TUTOR).
2. Implementar GET /students (TUTOR, solo sus alumnos).
3. Implementar POST /events (interno o TUTOR/ADMIN).
4. Insertar en learning_events con mínimos campos requeridos:

   * student_id
   * subject_id
   * term_id
   * activity_type_id
   * timestamp_start
   * is_correct opcional
5. (Opcional recomendado) Implementar GET /students/{id}/events (solo tutor del alumno).

### Smoke check Día 5

* Tutor crea alumno → 201
* Tutor lista alumnos → contiene el creado
* Insertar evento para ese alumno → 200/201
* Consultar eventos → aparece el insert

### Criterio “Día 5 completado” (cierre Sprint 0)

* Se puede crear alumno y registrar evento sin tocar DB manualmente.
* Todo en docker o documentado claramente.
* Documentación breve de endpoints usados y ejemplos curl.

---

## 4. Entregables finales de Sprint 0

Al final de Sprint 0 deben estar:

* docker-compose funcional
* DB con DDL + seeds
* backend FastAPI con:

  * /health y /health/db
  * /auth/login y /auth/me
  * /students (POST/GET)
  * /events (POST)
* RBAC funcionando
* Documento de evidencias (sprint0_log.md)

---

## 5. Puente hacia Sprint 1 (preparación)

Antes de iniciar Sprint 1, crear:

* una rama release/sprint0
* tag v0.1.0
* checklist de Sprint 1 (Doc 13 ya define alcance)

Sprint 1 comienza cuando Sprint 0 queda estable y repetible.

---

## 6. Nota final

Este plan está diseñado para evitar el error típico de:
“hacer pantallas primero”.

En este proyecto, la base es:
eventos → métricas → recomendaciones.

Cuando eso existe, el resto escala con mucha más seguridad.
