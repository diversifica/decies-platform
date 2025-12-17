# Documento 16 – Stack Técnico Concreto y Tareas Ejecutables
## Versión 1 (Execution Stack & Tasks V1)

## 1. Propósito del documento

Este documento define:
- El stack tecnológico concreto seleccionado.
- Las razones de cada decisión.
- La división del sistema en servicios reales.
- Las tareas técnicas ejecutables para iniciar el desarrollo.

A partir de este documento, el proyecto entra oficialmente en **fase de implementación**.

---

## 2. Criterios para la elección del stack

El stack se elige bajo los siguientes criterios:

1. Madurez y estabilidad.
2. Facilidad de contratación futura.
3. Buen soporte para APIs y procesamiento asíncrono.
4. Buen encaje con LLMs y pipelines de datos.
5. Escalabilidad sin sobreingeniería inicial.

---

## 3. Stack tecnológico seleccionado (V1)

### 3.1 Backend principal

- Lenguaje: **Python 3.12**
- Framework API: **FastAPI**
- Razones:
  - Alto rendimiento.
  - Tipado claro.
  - Ideal para APIs y LLM pipelines.
  - Fácil integración con tareas async.

---

### 3.2 Base de datos transaccional

- **PostgreSQL**
- ORM: **SQLAlchemy 2.x**
- Migraciones: **Alembic**

Razones:
- Modelo relacional sólido (Documento 07).
- Buen soporte para JSON y agregados.
- Escalabilidad probada.

---

### 3.3 Sistema de eventos

- Persistencia: **PostgreSQL (tabla append-only)**
- Cola asíncrona (opcional Fase 1.1): **Redis + RQ o Celery**

Razones:
- Simplicidad inicial.
- Posibilidad de re-procesar eventos.
- Migrable a Kafka en fases posteriores.

---

### 3.4 Motor de métricas

- Python puro (servicio interno).
- Ejecución:
  - Batch programado (cron)
  - O triggered por volumen de eventos.

Librerías:
- pandas (si volumen pequeño)
- numpy

---

### 3.5 Motor de recomendaciones

- Servicio Python interno.
- Reglas implementadas como:
  - Código explícito
  - Configuración versionada en YAML/JSON

No ML en V1.

---

### 3.6 Pipeline LLM

- Librería: **LangChain (ligero)** o implementación propia.
- Modelos:
  - API externa (ej. OpenAI, Gemini) o
  - Modelo local (Ollama) en fases posteriores.

Ejecución:
- Asíncrona.
- Totalmente trazada.

---

### 3.7 Frontend

#### Tutor y Admin
- Framework: **Next.js (React)**
- UI: básica, funcional, sin diseño avanzado.

#### Alumno
- Web simple integrada en Next.js.
- Sin PWA en Fase 1.

---

### 3.8 Autenticación

- JWT con expiración.
- Librería estándar FastAPI.
- Roles controlados en backend.

---

### 3.9 Infraestructura

- Contenedores: **Docker**
- Orquestación inicial: **docker-compose**
- Entorno:
  - dev
  - prod

No Kubernetes en Fase 1.

---

## 4. Estructura de repositorios

### Opción recomendada (monorepo)

/backend
/app
/api
/models
/services
/metrics
/recommendations
/llm
/events
/migrations
/frontend
/tutor
/student
/docker
/docs

---

## 5. Servicios internos (backend)

### 5.1 API Core
- Usuarios
- Alumnos
- Asignaturas
- Trimestres

### 5.2 Event Service
- Endpoint /events
- Validación mínima
- Escritura append-only

### 5.3 Metric Engine
- Procesa eventos
- Calcula MetricAggregate
- Actualiza MasteryState

### 5.4 Recommendation Engine
- Evalúa métricas
- Aplica reglas R01–R40
- Genera evidencias

### 5.5 LLM Pipeline
- Extract → Structure → Generate items
- Registro de ejecuciones

---

## 6. Tareas ejecutables – Sprint 0 (desglose técnico)

### Backend

- T0-BE-01: Crear proyecto FastAPI.
- T0-BE-02: Configurar PostgreSQL + Alembic.
- T0-BE-03: Implementar modelos User, Role, Student, Tutor.
- T0-BE-04: Implementar Subject, Term, Topic, MicroConcept.
- T0-BE-05: Implementar tabla LearningEvent.
- T0-BE-06: Endpoint POST /events.

### Infraestructura

- T0-INF-01: docker-compose backend + db.
- T0-INF-02: Variables de entorno.
- T0-INF-03: Documentar setup local.

---

## 7. Tareas ejecutables – Sprint 1 (desglose técnico)

### Backend

- T1-BE-01: ContentUpload endpoint.
- T1-BE-02: Almacenamiento de archivos.
- T1-BE-03: Pipeline LLM mínimo (extract text).
- T1-BE-04: Generación de ítems simples.
- T1-BE-05: ActivitySession + ActivitySessionItem.
- T1-BE-06: MetricEngine V1 (accuracy, mastery).
- T1-BE-07: RecommendationEngine V1 (R01, R11, R21).

### Frontend Tutor

- T1-FE-T-01: Crear alumno.
- T1-FE-T-02: Subir contenido.
- T1-FE-T-03: Ver recomendaciones.
- T1-FE-T-04: Aceptar/rechazar recomendación.

### Frontend Alumno

- T1-FE-A-01: Vista de quiz.
- T1-FE-A-02: Envío de respuestas.
- T1-FE-A-03: Feedback inmediato.

---

## 8. Criterios de éxito técnico inicial

- Un alumno genera eventos reales.
- Métricas se recalculan correctamente.
- Se genera al menos una recomendación explicable.
- El tutor puede decidir.
- Todo es trazable de extremo a extremo.

---

## 9. Decisiones explícitas (para no discutir después)

- No ML en recomendaciones V1.
- No UX avanzada.
- No múltiples juegos.
- No optimización prematura.
- No automatización sin tutor.

---

## 10. Próximos documentos técnicos opcionales

- Documento 17 – Especificación de API (OpenAPI)
- Documento 18 – Esquema de Base de Datos (DDL)
- Documento 19 – Prompt Book del Pipeline LLM
- Documento 20 – Plan de Testing y Validación

---

## 11. Nota final

Este documento marca el paso definitivo de diseño a ejecución.

A partir de aquí, cualquier avance es código, pruebas y validación real.
El diseño ya está hecho. Ahora se construye.
