# Documento 17 – Especificación de API (OpenAPI)
## Versión 1 (API Specification V1)

## 1. Propósito del documento

Este documento define la **especificación funcional de la API** del sistema para la Fase 1, alineada con:

- Documento 07 – Modelo de Datos
- Documento 08 – Arquitectura Lógica
- Documento 12 – Arquitectura Técnica
- Documento 16 – Stack Técnico Concreto

El objetivo es:
- Permitir desarrollo paralelo frontend/backend.
- Definir contratos claros y estables.
- Reducir ambigüedades de implementación.

Esta especificación describe **endpoints, payloads y respuestas**, no detalles internos de código.

---

## 2. Convenciones generales

### 2.1 Base URL

### 2.2 Autenticación
- Tipo: Bearer JWT
- Header:

### 2.3 Roles
- PLAYER (Alumno)
- TUTOR
- ADMIN

El backend valida permisos en cada endpoint.

---

## 3. Autenticación y usuarios

### POST /auth/login
Autentica un usuario y devuelve token JWT.

**Request**
```json
{
  "email": "string",
  "password": "string"
}

{
  "access_token": "string",
  "token_type": "bearer",
  "expires_in": 3600,
  "roles": ["TUTOR"]
}

GET /auth/me

Devuelve el usuario autenticado.

Response 200

{
  "id": "uuid",
  "email": "string",
  "roles": ["TUTOR"]
}

4. Gestión de alumnos y tutores
POST /students

Crear un alumno (TUTOR).

Request

{
  "display_name": "string",
  "school_level": "ESO"
}


Response 201

{
  "id": "uuid",
  "display_name": "string"
}

GET /students

Listar alumnos del tutor.

Response 200

[
  {
    "id": "uuid",
    "display_name": "string",
    "school_level": "ESO"
  }
]

GET /students/{student_id}

Detalle de alumno.

5. Estructura académica
GET /subjects

Listar asignaturas.

Response 200

[
  {
    "id": "uuid",
    "code": "MAT",
    "name": "Matemáticas"
  }
]

GET /terms

Listar trimestres activos.

POST /students/{student_id}/context

Asignar contexto académico al alumno.

Request

{
  "subject_ids": ["uuid"],
  "term_id": "uuid"
}

6. Ingesta de contenido académico
POST /content/uploads

Subir contenido (PDF o imagen).

Request

multipart/form-data

file

student_id

subject_id

term_id

topic_id (opcional)

Response 201

{
  "id": "uuid",
  "status": "uploaded"
}

GET /content/uploads

Listar contenidos subidos por el tutor.

7. Pipeline LLM (control y estado)
POST /llm/process/{content_upload_id}

Lanzar procesamiento LLM (ADMIN o sistema).

Response 202

{
  "status": "processing",
  "run_id": "uuid"
}

GET /llm/runs/{run_id}

Estado de una ejecución LLM.

Response 200

{
  "run_id": "uuid",
  "status": "success",
  "model": "string",
  "prompt_version": "v1"
}

8. Ítems y actividades
GET /items

Listar ítems (uso interno / admin).

POST /activities/sessions

Crear una sesión de actividad para un alumno.

Request

{
  "student_id": "uuid",
  "activity_type": "QUIZ",
  "subject_id": "uuid",
  "term_id": "uuid"
}


Response 201

{
  "session_id": "uuid",
  "items": [
    {
      "session_item_id": "uuid",
      "stem": "string",
      "options": ["A", "B", "C"]
    }
  ]
}

9. Juego y envío de respuestas (Alumno)
POST /activities/sessions/{session_id}/responses

Enviar respuesta a un ítem.

Request

{
  "session_item_id": "uuid",
  "response": "string",
  "used_hint": false
}


Response 200

{
  "is_correct": true,
  "feedback": "string"
}


Este endpoint genera automáticamente un LearningEvent.

POST /activities/sessions/{session_id}/end

Finalizar sesión.

10. Eventos de aprendizaje (interno)
POST /events

Registro explícito de eventos (uso sistema).

Request

{
  "student_id": "uuid",
  "event_type": "ANSWER",
  "item_id": "uuid",
  "is_correct": true,
  "duration_ms": 1200
}

11. Métricas y estado de dominio
GET /students/{student_id}/mastery

Estado de dominio por microconcepto.

Response 200

[
  {
    "microconcept_id": "uuid",
    "mastery_score": 0.72,
    "status": "in_progress"
  }
]

GET /students/{student_id}/metrics

Métricas agregadas (uso tutor).

12. Recomendaciones
GET /students/{student_id}/recommendations

Listar recomendaciones activas.

Response 200

[
  {
    "id": "uuid",
    "code": "R01",
    "title": "Priorizar microconceptos en riesgo",
    "priority": "high",
    "evidence": [
      {
        "metric": "mastery_score",
        "value": 0.32
      }
    ]
  }
]

POST /recommendations/{recommendation_id}/decision

Decisión del tutor.

Request

{
  "decision": "accepted",
  "comment": "string"
}

13. Informes al tutor
GET /reports

Listar informes disponibles.

GET /reports/{report_id}

Obtener informe completo.

Response 200

{
  "report_id": "uuid",
  "summary": "string",
  "sections": [
    {
      "code": "EXEC_SUMMARY",
      "content": "string"
    }
  ]
}

14. Notas reales y evaluación externa
POST /grades

Registrar nota real (Tutor).

Request

{
  "student_id": "uuid",
  "subject_id": "uuid",
  "term_id": "uuid",
  "grade_value": 6.5
}

15. Errores y códigos de estado

200 OK

201 Created

202 Accepted

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

500 Internal Server Error

Errores devueltos en formato:

{
  "error": "string",
  "detail": "string"
}

16. Versionado de la API

Cambios incompatibles → nueva versión (/api/v2)

Campos nuevos → compatibles hacia atrás

Campos obsoletos → marcados pero no eliminados en V1

17. Nota final

Esta especificación define el contrato mínimo para Fase 1.

Cualquier endpoint adicional debe:

alinearse con el modelo de datos

respetar roles y trazabilidad

añadirse como versión incrementada del documento


---

Con el **Documento 17** ya puedes:

- generar automáticamente clientes frontend
- crear tests de contrato
- arrancar FastAPI con OpenAPI nativo
- dividir trabajo entre frontend y backend sin bloqueos
