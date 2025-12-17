# Documento 07 – Modelo de Datos y Entidades del Sistema
## Versión 1 (Data Model V1)

## 1. Propósito

Este documento define el **modelo de datos conceptual (entidades, relaciones y campos clave)** necesario para implementar el sistema de aprendizaje adaptativo gamificado, alineado con:

- Documento 01: Objetivo Rector y Principios
- Documento 02: Métricas del Alumno V1
- Documento 04: Motor de Recomendaciones V1
- Documento 05–06: Catálogo y Mapeo de Recomendaciones V1

El modelo está diseñado para:
- Trazabilidad completa (eventos crudos → métricas → recomendaciones → informe).
- Escalabilidad (más cursos, asignaturas, juegos, métricas).
- Explicabilidad (por qué se recomienda X).
- Evolución sin ruptura (versionado de contenido, métricas y reglas).

---

## 2. Convenciones generales

### 2.1 Identificadores
- Todas las entidades usan `id` único (UUID o ULID recomendado).
- Entidades de catálogo (asignaturas, tipos de juego, recomendaciones) usan además un `code` estable (ej. `R21`).

### 2.2 Versionado
- El contenido estructurado generado por LLM y los ítems derivados deben ser **versionables**.
- Reglas y umbrales del motor deben quedar registrados con `engine_version` y `ruleset_version`.

### 2.3 Trazabilidad
Toda recomendación e informe debe poder rastrearse a:
- eventos crudos
- agregados de métricas
- reglas disparadoras
- versión del catálogo de recomendaciones

### 2.4 Multi-ámbito académico
El modelo debe permitir segmentación por:
- asignatura
- trimestre/evaluación
- tema
- microconcepto

---

## 3. Entidades principales

### 3.1 Usuarios y roles

#### User
Representa una cuenta del sistema.
- `id`
- `email` (único)
- `password_hash` (o proveedor SSO)
- `status` (active, disabled)
- `created_at`, `updated_at`

#### Role
Catálogo de roles.
- `id`
- `code` (PLAYER, TUTOR, ADMIN)
- `name`

#### UserRole
Relación N:N usuario-rol.
- `id`
- `user_id`
- `role_id`

---

### 3.2 Alumno, tutor y familia

#### Student
Perfil del alumno (jugador).
- `id`
- `user_id` (opcional si el alumno inicia sesión; si no, puede ser perfil sin credenciales)
- `display_name`
- `birth_year` (opcional)
- `school_level` (ej. ESO)
- `created_at`, `updated_at`

#### Tutor
Perfil del tutor/padre/madre.
- `id`
- `user_id`
- `display_name`
- `created_at`, `updated_at`

#### StudentTutorLink
Vinculación tutor-alumno (N:N).
- `id`
- `student_id`
- `tutor_id`
- `relationship` (padre, madre, tutor legal, etc.)
- `permissions` (view_only, manage_content, manage_plan, etc.)
- `created_at`

---

## 4. Estructura académica

### 4.1 Catálogos académicos

#### AcademicYear
Define un curso académico.
- `id`
- `name` (ej. 2025-2026)
- `start_date`, `end_date`
- `status` (active, archived)

#### Subject
Asignaturas.
- `id`
- `code` (MAT, LEN, HIS, etc.)
- `name`
- `level` (Primaria/ESO)
- `active`

#### Term
Trimestres/evaluaciones.
- `id`
- `academic_year_id`
- `code` (T1, T2, T3)
- `name`
- `start_date`, `end_date`
- `status`

#### Topic
Tema de una asignatura.
- `id`
- `subject_id`
- `term_id` (opcional si el tema se asocia a un trimestre concreto)
- `code` (opcional)
- `name`
- `order_index`

#### MicroConcept
Unidad mínima evaluable (base de métricas y conocimiento).
- `id`
- `subject_id`
- `term_id` (opcional)
- `topic_id` (opcional)
- `code` (opcional)
- `name`
- `description` (opcional)
- `prerequisite_ids` (lista o tabla relacional, recomendado tabla aparte)
- `active`

#### MicroConceptPrerequisite
Relación de prerequisitos.
- `id`
- `microconcept_id`
- `prerequisite_microconcept_id`

---

## 5. Ingesta de contenido (tutor) y estructuración (LLM)

### 5.1 Archivos originales

#### ContentUpload
Registro de subida (PDF, imagen).
- `id`
- `tutor_id`
- `student_id` (si el contenido es para un alumno concreto)
- `subject_id`
- `term_id`
- `topic_id` (opcional)
- `upload_type` (pdf, image)
- `storage_uri` (ruta/URL interna)
- `file_name`
- `mime_type`
- `page_count` (si aplica)
- `created_at`

### 5.2 Extracción y normalización

#### ContentExtraction
Resultado de extracción (texto/estructura de base).
- `id`
- `content_upload_id`
- `extraction_method` (pdf_text, vision_ocr, hybrid)
- `raw_text_uri` (opcional)
- `quality_score` (opcional)
- `created_at`

### 5.3 Contenido estructurado (LLM)

#### KnowledgeEntry
Unidad de conocimiento estructurado derivada de un upload.
- `id`
- `student_id` (si es personalizado) o `null` (si es genérico)
- `subject_id`
- `term_id`
- `topic_id` (opcional)
- `source_upload_id` (ContentUpload)
- `entry_version`
- `status` (draft, approved, archived)
- `created_at`, `updated_at`

#### KnowledgeChunk
Fragmentos estructurados dentro de una entrada.
- `id`
- `knowledge_entry_id`
- `chunk_type` (definition, example, rule, summary, exercise_seed, note)
- `content` (texto estructurado)
- `microconcept_id` (si se pudo mapear)
- `confidence` (0–1, opcional)
- `order_index`

#### LLMRun
Ejecución del pipeline LLM (auditoría y trazabilidad).
- `id`
- `run_type` (extract, structure, generate_items, analyze_metrics, generate_report)
- `input_refs` (JSON con ids de entidades usadas)
- `output_refs` (JSON con ids generados)
- `model_name`
- `prompt_version`
- `engine_version` (versión del sistema)
- `status` (success, error)
- `started_at`, `finished_at`
- `error_message` (si aplica)

---

## 6. Banco de ítems y actividades (juegos/tests)

### 6.1 Ítems evaluables

#### Item
Pregunta/ejercicio atómico.
- `id`
- `subject_id`
- `term_id`
- `topic_id` (opcional)
- `microconcept_id` (recomendado)
- `item_type` (mcq, true_false, match, fill_blank, short_answer, etc.)
- `stem` (enunciado)
- `options` (JSON si aplica)
- `correct_answer` (normalizado)
- `explanation` (opcional)
- `difficulty` (escala interna)
- `source_knowledge_entry_id` (trazabilidad)
- `item_version`
- `status` (active, deprecated)

#### ItemTag
Etiquetas para análisis (tipo examen, transferencia, visual, etc.).
- `id`
- `item_id`
- `tag_code`

### 6.2 Actividades y sesiones

#### ActivityType
Catálogo de tipos de actividad/juego.
- `id`
- `code` (QUIZ, MATCH, CLOZE, REVIEW, EXAM_STYLE)
- `name`

#### ActivitySession
Sesión de juego/aprendizaje.
- `id`
- `student_id`
- `activity_type_id`
- `subject_id`
- `term_id`
- `topic_id` (opcional)
- `started_at`
- `ended_at`
- `device_type` (opcional)
- `status` (completed, abandoned)

#### ActivitySessionItem
Ítems presentados en una sesión (orden y contexto).
- `id`
- `session_id`
- `item_id`
- `order_index`
- `presented_at`

---

## 7. Eventos crudos (Nivel 0) y analítica

### 7.1 Evento de interacción

#### LearningEvent
Evento crudo por interacción (append-only).
- `id`
- `student_id`
- `session_id`
- `subject_id`
- `term_id`
- `topic_id` (opcional)
- `microconcept_id` (si aplica)
- `activity_type_id`
- `item_id`
- `timestamp_start`
- `timestamp_end`
- `duration_ms`
- `attempt_number`
- `response_normalized`
- `is_correct`
- `hint_used` (none, hint, explanation, theory)
- `difficulty_at_time`
- `created_at`

Nota: este evento es la fuente única de verdad para recalcular métricas.

### 7.2 Agregados de métricas

#### MetricAggregate
Agregado por ventana temporal y ámbito.
- `id`
- `student_id`
- `scope_type` (subject, term, topic, microconcept, activity_type)
- `scope_id`
- `window_start`, `window_end`
- `accuracy`
- `first_attempt_accuracy`
- `error_rate`
- `median_response_time_ms`
- `attempts_per_item_avg`
- `hint_rate`
- `abandon_rate` (si aplica)
- `fatigue_slope` (si aplica)
- `retention_score` (si aplica)
- `computed_at`
- `metrics_version` (ej. V1)

#### MasteryState
Estado actual por microconcepto (vista materializada o tabla).
- `id`
- `student_id`
- `microconcept_id`
- `mastery_score` (0–1)
- `status` (dominant, in_progress, at_risk)
- `last_practice_at`
- `recommended_next_review_at` (opcional)
- `updated_at`
- `metrics_version`

---

## 8. Recomendaciones, decisiones del tutor e impacto

### 8.1 Recomendación emitida

#### RecommendationCatalog
Catálogo cerrado (R01–R40).
- `id`
- `code` (R01..R40)
- `title`
- `description`
- `category` (focus, strategy, dosage, external_validation)
- `active`
- `catalog_version` (V1)

#### RecommendationInstance
Recomendación concreta generada para un alumno.
- `id`
- `student_id`
- `subject_id`
- `term_id`
- `topic_id` (opcional)
- `microconcept_id` (opcional)
- `recommendation_code` (FK a catálogo por code)
- `priority` (high, medium, low)
- `status` (proposed, accepted, rejected, expired, completed)
- `generated_at`
- `engine_version`
- `ruleset_version`
- `evaluation_window_days` (por defecto 14)

#### RecommendationEvidence
Evidencias asociadas a una recomendación (para explicabilidad).
- `id`
- `recommendation_instance_id`
- `metric_name` (accuracy, mastery_score, hint_rate, retention_score, etc.)
- `metric_value`
- `metric_window_start`, `metric_window_end`
- `note` (opcional)

### 8.2 Decisión y seguimiento

#### TutorDecision
Decisión explícita del tutor sobre una recomendación.
- `id`
- `recommendation_instance_id`
- `tutor_id`
- `decision` (accepted, rejected, postponed)
- `comment` (opcional)
- `decided_at`

#### RecommendationOutcome
Evaluación del efecto tras la ventana.
- `id`
- `recommendation_instance_id`
- `evaluation_start`, `evaluation_end`
- `success` (true/false/partial)
- `delta_mastery`
- `delta_retention`
- `delta_accuracy`
- `delta_hint_rate` (si aplica)
- `computed_at`
- `notes` (opcional)

---

## 9. Informes al tutor

#### TutorReport
Informe generado.
- `id`
- `student_id`
- `tutor_id`
- `subject_id`
- `term_id`
- `report_type` (weekly, on_demand, term_end)
- `period_start`, `period_end`
- `summary_text`
- `generated_at`
- `engine_version`
- `ruleset_version`

#### TutorReportSection
Secciones del informe (para render flexible).
- `id`
- `report_id`
- `section_code` (EXEC_SUMMARY, CURRENT_STATE, TRENDS, STRATEGIES, REAL_GRADES, RECOMMENDATIONS, FOLLOW_UP)
- `content` (JSON o texto estructurado)
- `order_index`

---

## 10. Notas reales, observaciones y alineación externa

#### RealGrade
Calificación real introducida por tutor.
- `id`
- `student_id`
- `subject_id`
- `term_id`
- `assessment_date`
- `grade_value` (numérico o escala)
- `grading_scale` (0-10, A-F, etc.)
- `notes` (opcional)
- `created_by_tutor_id`
- `created_at`

#### AssessmentScopeTag
Etiquetado de qué se evaluó (para discrepancias).
- `id`
- `real_grade_id`
- `topic_id` (opcional)
- `microconcept_id` (opcional)
- `weight` (opcional)

---

## 11. Experimentación (A/B ligero)

#### Experiment
Definición de experimento.
- `id`
- `student_id` (V1 puede ser por alumno; V2 podría ser global)
- `subject_id`
- `term_id`
- `scope_type` (microconcept, topic)
- `scope_id`
- `variant_a` (activity_type_id o configuración)
- `variant_b`
- `start_date`, `end_date`
- `status` (running, completed, cancelled)

#### ExperimentResult
Resultados comparativos.
- `id`
- `experiment_id`
- `metric_primary` (retention_score o delta_mastery)
- `variant_a_value`
- `variant_b_value`
- `winner` (A, B, none)
- `computed_at`

---

## 12. Configuración y personalización

#### StudentSettings
Preferencias y restricciones del alumno/tutor.
- `id`
- `student_id`
- `weekly_time_budget_minutes`
- `session_max_minutes`
- `preferred_activity_types` (JSON)
- `notifications_enabled`
- `updated_at`

#### SystemConfig
Parámetros globales versionables.
- `id`
- `config_key`
- `config_value` (JSON)
- `config_version`
- `updated_at`

---

## 13. Auditoría, privacidad y cumplimiento

#### AuditLog
Registro de acciones críticas.
- `id`
- `actor_user_id`
- `action_code` (UPLOAD_CONTENT, GENERATE_REPORT, ACCEPT_RECOMMENDATION, etc.)
- `entity_type`
- `entity_id`
- `metadata` (JSON)
- `created_at`

#### DataRetentionPolicy
Política de retención (opcional en V1, recomendable para escalar).
- `id`
- `entity_type`
- `retention_days`
- `anonymize_after_days`

---

## 14. Relaciones clave (resumen)

- User 1..N UserRole N..1 Role
- Tutor N..N Student (StudentTutorLink)
- AcademicYear 1..N Term
- Subject 1..N Topic 1..N MicroConcept
- ContentUpload 1..1 ContentExtraction 1..N KnowledgeEntry 1..N KnowledgeChunk
- KnowledgeEntry 1..N Item
- Student 1..N ActivitySession 1..N LearningEvent
- LearningEvent → MetricAggregate / MasteryState (derivados)
- MasteryState + MetricAggregate → RecommendationInstance (Motor)
- RecommendationInstance 1..N RecommendationEvidence
- RecommendationInstance 0..1 TutorDecision
- RecommendationInstance 0..1 RecommendationOutcome
- TutorReport 1..N TutorReportSection
- RealGrade 1..N AssessmentScopeTag

---

## 15. Implementación mínima recomendada para Fase 1

Entidades mínimas imprescindibles para entregar valor real:

- User, Role, UserRole
- Student, Tutor, StudentTutorLink
- Subject, Term, Topic, MicroConcept
- ContentUpload (y opcional ContentExtraction)
- KnowledgeEntry, KnowledgeChunk
- Item, ActivityType
- ActivitySession, LearningEvent
- MetricAggregate, MasteryState
- RecommendationCatalog, RecommendationInstance, RecommendationEvidence
- TutorDecision
- TutorReport, TutorReportSection
- RealGrade

El resto puede introducirse progresivamente sin romper el diseño.

---

## 16. Nota final

Este modelo de datos está diseñado para:
- soportar el ciclo completo: contenido → práctica → eventos → métricas → recomendaciones → informe → evaluación
- habilitar personalización progresiva basada en datos
- mantener explicabilidad y control del tutor como principio no negociable

Cualquier cambio estructural debe reflejarse en una nueva versión del documento.
