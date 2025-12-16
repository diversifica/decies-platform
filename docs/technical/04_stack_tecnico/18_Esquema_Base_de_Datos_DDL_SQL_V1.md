# Documento 18 – Esquema de Base de Datos (DDL SQL)

## Versión 1 (DB Schema V1 – PostgreSQL)

## 1. Propósito

Este documento define un **DDL inicial (PostgreSQL)** para Fase 1, alineado con:

* Documento 07 (Modelo de Datos)
* Documento 16 (Stack técnico concreto)
* Documento 17 (API)

El objetivo es tener un esquema:

* Relacional, trazable y versionable
* Suficiente para Sprint 0 y Sprint 1
* Extensible para fases posteriores

Notas:

* Se usa `uuid` como PK.
* Se incluyen `created_at` y `updated_at` en tablas principales.
* En Fase 1, algunos catálogos se mantienen simples y ampliables.

---

## 2. DDL (PostgreSQL)

```sql
-- ============================================================
-- Documento 18 - DDL PostgreSQL V1
-- ============================================================

-- Recomendado
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMs
-- ============================================================

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_status') THEN
    CREATE TYPE user_status AS ENUM ('active','disabled');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'content_upload_type') THEN
    CREATE TYPE content_upload_type AS ENUM ('pdf','image');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'llm_run_status') THEN
    CREATE TYPE llm_run_status AS ENUM ('success','error','processing');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'knowledge_entry_status') THEN
    CREATE TYPE knowledge_entry_status AS ENUM ('draft','approved','archived');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'activity_session_status') THEN
    CREATE TYPE activity_session_status AS ENUM ('completed','abandoned');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'hint_used_type') THEN
    CREATE TYPE hint_used_type AS ENUM ('none','hint','explanation','theory');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scope_type') THEN
    CREATE TYPE scope_type AS ENUM ('subject','term','topic','microconcept','activity_type');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'mastery_status') THEN
    CREATE TYPE mastery_status AS ENUM ('dominant','in_progress','at_risk');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recommendation_priority') THEN
    CREATE TYPE recommendation_priority AS ENUM ('high','medium','low');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'recommendation_status') THEN
    CREATE TYPE recommendation_status AS ENUM ('proposed','accepted','rejected','postponed','expired','completed');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'tutor_decision_type') THEN
    CREATE TYPE tutor_decision_type AS ENUM ('accepted','rejected','postponed');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_type') THEN
    CREATE TYPE report_type AS ENUM ('weekly','on_demand','term_end');
  END IF;

  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'school_level') THEN
    CREATE TYPE school_level AS ENUM ('ESO');
  END IF;
END $$;

-- ============================================================
-- USERS & ROLES
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  email text NOT NULL UNIQUE,
  password_hash text NOT NULL,
  status user_status NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS roles (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  code text NOT NULL UNIQUE, -- PLAYER, TUTOR, ADMIN
  name text NOT NULL
);

CREATE TABLE IF NOT EXISTS user_roles (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role_id uuid NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (user_id, role_id)
);

-- ============================================================
-- TUTOR & STUDENT
-- ============================================================

CREATE TABLE IF NOT EXISTS tutors (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
  display_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS students (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id uuid UNIQUE REFERENCES users(id) ON DELETE SET NULL, -- opcional
  display_name text NOT NULL,
  birth_year int NULL,
  school_level school_level NOT NULL DEFAULT 'ESO',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS student_tutor_links (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  tutor_id uuid NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  relationship text NULL, -- padre/madre/tutor legal
  permissions jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (student_id, tutor_id)
);

-- ============================================================
-- ACADEMIC STRUCTURE
-- ============================================================

CREATE TABLE IF NOT EXISTS academic_years (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  name text NOT NULL, -- "2025-2026"
  start_date date NOT NULL,
  end_date date NOT NULL,
  status text NOT NULL DEFAULT 'active', -- simple en V1
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(name)
);

CREATE TABLE IF NOT EXISTS subjects (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  code text NOT NULL UNIQUE, -- MAT, LEN, HIS...
  name text NOT NULL,
  level text NOT NULL DEFAULT 'ESO',
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS terms (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  academic_year_id uuid REFERENCES academic_years(id) ON DELETE CASCADE,
  code text NOT NULL, -- T1, T2, T3
  name text NOT NULL,
  start_date date NULL,
  end_date date NULL,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (academic_year_id, code)
);

CREATE TABLE IF NOT EXISTS topics (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  term_id uuid NULL REFERENCES terms(id) ON DELETE SET NULL,
  code text NULL,
  name text NOT NULL,
  order_index int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS microconcepts (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
  term_id uuid NULL REFERENCES terms(id) ON DELETE SET NULL,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  code text NULL,
  name text NOT NULL,
  description text NULL,
  active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS microconcept_prerequisites (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  microconcept_id uuid NOT NULL REFERENCES microconcepts(id) ON DELETE CASCADE,
  prerequisite_microconcept_id uuid NOT NULL REFERENCES microconcepts(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (microconcept_id, prerequisite_microconcept_id)
);

-- Contexto del alumno (Fase 1 simplificado)
CREATE TABLE IF NOT EXISTS student_context (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  subject_ids uuid[] NOT NULL DEFAULT '{}'::uuid[],
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (student_id)
);

-- ============================================================
-- CONTENT UPLOADS & LLM PIPELINE
-- ============================================================

CREATE TABLE IF NOT EXISTS content_uploads (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  tutor_id uuid NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  student_id uuid NULL REFERENCES students(id) ON DELETE SET NULL,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  upload_type content_upload_type NOT NULL,
  storage_uri text NOT NULL,
  file_name text NOT NULL,
  mime_type text NOT NULL,
  page_count int NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_extractions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  content_upload_id uuid NOT NULL UNIQUE REFERENCES content_uploads(id) ON DELETE CASCADE,
  extraction_method text NOT NULL, -- pdf_text, vision_ocr, hybrid
  raw_text_uri text NULL,
  quality_score numeric(5,2) NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_entries (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NULL REFERENCES students(id) ON DELETE SET NULL, -- null = genérico
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  source_upload_id uuid NOT NULL REFERENCES content_uploads(id) ON DELETE RESTRICT,
  entry_version int NOT NULL DEFAULT 1,
  status knowledge_entry_status NOT NULL DEFAULT 'draft',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  knowledge_entry_id uuid NOT NULL REFERENCES knowledge_entries(id) ON DELETE CASCADE,
  chunk_type text NOT NULL, -- definition/example/rule/summary/exercise_seed/note
  content text NOT NULL,
  microconcept_id uuid NULL REFERENCES microconcepts(id) ON DELETE SET NULL,
  confidence numeric(5,4) NULL,
  order_index int NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS llm_runs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  run_type text NOT NULL, -- extract/structure/generate_items/analyze_metrics/generate_report
  input_refs jsonb NOT NULL DEFAULT '{}'::jsonb,
  output_refs jsonb NOT NULL DEFAULT '{}'::jsonb,
  model_name text NOT NULL,
  prompt_version text NOT NULL,
  engine_version text NOT NULL,
  status llm_run_status NOT NULL DEFAULT 'processing',
  started_at timestamptz NOT NULL DEFAULT now(),
  finished_at timestamptz NULL,
  error_message text NULL
);

-- ============================================================
-- ITEMS & ACTIVITIES
-- ============================================================

CREATE TABLE IF NOT EXISTS activity_types (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  code text NOT NULL UNIQUE, -- QUIZ, MATCH, CLOZE, REVIEW, EXAM_STYLE
  name text NOT NULL
);

CREATE TABLE IF NOT EXISTS items (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  microconcept_id uuid NULL REFERENCES microconcepts(id) ON DELETE SET NULL,
  item_type text NOT NULL, -- mcq/true_false/match/fill_blank/short_answer
  stem text NOT NULL,
  options jsonb NULL,
  correct_answer text NOT NULL,
  explanation text NULL,
  difficulty numeric(5,4) NULL,
  source_knowledge_entry_id uuid NULL REFERENCES knowledge_entries(id) ON DELETE SET NULL,
  item_version int NOT NULL DEFAULT 1,
  status text NOT NULL DEFAULT 'active',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS item_tags (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  item_id uuid NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  tag_code text NOT NULL,
  UNIQUE(item_id, tag_code)
);

CREATE TABLE IF NOT EXISTS activity_sessions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  activity_type_id uuid NOT NULL REFERENCES activity_types(id) ON DELETE RESTRICT,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  started_at timestamptz NOT NULL DEFAULT now(),
  ended_at timestamptz NULL,
  status activity_session_status NULL
);

CREATE TABLE IF NOT EXISTS activity_session_items (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id uuid NOT NULL REFERENCES activity_sessions(id) ON DELETE CASCADE,
  item_id uuid NOT NULL REFERENCES items(id) ON DELETE RESTRICT,
  order_index int NOT NULL DEFAULT 0,
  presented_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- LEARNING EVENTS (append-only)
-- ============================================================

CREATE TABLE IF NOT EXISTS learning_events (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  session_id uuid NULL REFERENCES activity_sessions(id) ON DELETE SET NULL,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  microconcept_id uuid NULL REFERENCES microconcepts(id) ON DELETE SET NULL,
  activity_type_id uuid NOT NULL REFERENCES activity_types(id) ON DELETE RESTRICT,
  item_id uuid NULL REFERENCES items(id) ON DELETE SET NULL,
  timestamp_start timestamptz NOT NULL DEFAULT now(),
  timestamp_end timestamptz NULL,
  duration_ms int NULL,
  attempt_number int NOT NULL DEFAULT 1,
  response_normalized text NULL,
  is_correct boolean NULL,
  hint_used hint_used_type NOT NULL DEFAULT 'none',
  difficulty_at_time numeric(5,4) NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_learning_events_student_time
  ON learning_events(student_id, timestamp_start DESC);

CREATE INDEX IF NOT EXISTS idx_learning_events_scope
  ON learning_events(student_id, subject_id, term_id);

-- ============================================================
-- METRICS & MASTERY
-- ============================================================

CREATE TABLE IF NOT EXISTS metric_aggregates (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  scope_type scope_type NOT NULL,
  scope_id uuid NOT NULL,
  window_start timestamptz NOT NULL,
  window_end timestamptz NOT NULL,
  accuracy numeric(6,4) NULL,
  first_attempt_accuracy numeric(6,4) NULL,
  error_rate numeric(6,4) NULL,
  median_response_time_ms int NULL,
  attempts_per_item_avg numeric(8,4) NULL,
  hint_rate numeric(6,4) NULL,
  abandon_rate numeric(6,4) NULL,
  fatigue_slope numeric(10,6) NULL,
  retention_score numeric(6,4) NULL,
  computed_at timestamptz NOT NULL DEFAULT now(),
  metrics_version text NOT NULL DEFAULT 'V1',
  UNIQUE(student_id, scope_type, scope_id, window_start, window_end, metrics_version)
);

CREATE INDEX IF NOT EXISTS idx_metric_aggregates_student_scope
  ON metric_aggregates(student_id, scope_type, scope_id);

CREATE TABLE IF NOT EXISTS mastery_states (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  microconcept_id uuid NOT NULL REFERENCES microconcepts(id) ON DELETE CASCADE,
  mastery_score numeric(6,4) NOT NULL DEFAULT 0,
  status mastery_status NOT NULL DEFAULT 'in_progress',
  last_practice_at timestamptz NULL,
  recommended_next_review_at timestamptz NULL,
  updated_at timestamptz NOT NULL DEFAULT now(),
  metrics_version text NOT NULL DEFAULT 'V1',
  UNIQUE(student_id, microconcept_id, metrics_version)
);

CREATE INDEX IF NOT EXISTS idx_mastery_states_student
  ON mastery_states(student_id);

-- ============================================================
-- RECOMMENDATIONS
-- ============================================================

CREATE TABLE IF NOT EXISTS recommendation_catalog (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  code text NOT NULL UNIQUE, -- R01..R40
  title text NOT NULL,
  description text NOT NULL,
  category text NOT NULL, -- focus/strategy/dosage/external_validation
  active boolean NOT NULL DEFAULT true,
  catalog_version text NOT NULL DEFAULT 'V1'
);

CREATE TABLE IF NOT EXISTS recommendation_instances (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  microconcept_id uuid NULL REFERENCES microconcepts(id) ON DELETE SET NULL,
  recommendation_code text NOT NULL REFERENCES recommendation_catalog(code) ON DELETE RESTRICT,
  priority recommendation_priority NOT NULL DEFAULT 'medium',
  status recommendation_status NOT NULL DEFAULT 'proposed',
  generated_at timestamptz NOT NULL DEFAULT now(),
  engine_version text NOT NULL DEFAULT 'V1',
  ruleset_version text NOT NULL DEFAULT 'V1',
  evaluation_window_days int NOT NULL DEFAULT 14
);

CREATE INDEX IF NOT EXISTS idx_recommendation_instances_student
  ON recommendation_instances(student_id, status, generated_at DESC);

CREATE TABLE IF NOT EXISTS recommendation_evidence (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  recommendation_instance_id uuid NOT NULL REFERENCES recommendation_instances(id) ON DELETE CASCADE,
  metric_name text NOT NULL,
  metric_value numeric(12,6) NULL,
  metric_window_start timestamptz NULL,
  metric_window_end timestamptz NULL,
  note text NULL
);

CREATE TABLE IF NOT EXISTS tutor_decisions (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  recommendation_instance_id uuid NOT NULL UNIQUE REFERENCES recommendation_instances(id) ON DELETE CASCADE,
  tutor_id uuid NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  decision tutor_decision_type NOT NULL,
  comment text NULL,
  decided_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendation_outcomes (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  recommendation_instance_id uuid NOT NULL UNIQUE REFERENCES recommendation_instances(id) ON DELETE CASCADE,
  evaluation_start timestamptz NOT NULL,
  evaluation_end timestamptz NOT NULL,
  success text NOT NULL, -- true/false/partial (string simple V1)
  delta_mastery numeric(10,6) NULL,
  delta_retention numeric(10,6) NULL,
  delta_accuracy numeric(10,6) NULL,
  delta_hint_rate numeric(10,6) NULL,
  computed_at timestamptz NOT NULL DEFAULT now(),
  notes text NULL
);

-- ============================================================
-- REPORTS
-- ============================================================

CREATE TABLE IF NOT EXISTS tutor_reports (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  tutor_id uuid NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  report_type report_type NOT NULL,
  period_start date NOT NULL,
  period_end date NOT NULL,
  summary_text text NOT NULL DEFAULT '',
  generated_at timestamptz NOT NULL DEFAULT now(),
  engine_version text NOT NULL DEFAULT 'V1',
  ruleset_version text NOT NULL DEFAULT 'V1'
);

CREATE TABLE IF NOT EXISTS tutor_report_sections (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  report_id uuid NOT NULL REFERENCES tutor_reports(id) ON DELETE CASCADE,
  section_code text NOT NULL, -- EXEC_SUMMARY, CURRENT_STATE, ...
  content jsonb NOT NULL DEFAULT '{}'::jsonb,
  order_index int NOT NULL DEFAULT 0
);

-- ============================================================
-- REAL GRADES
-- ============================================================

CREATE TABLE IF NOT EXISTS real_grades (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  student_id uuid NOT NULL REFERENCES students(id) ON DELETE CASCADE,
  subject_id uuid NOT NULL REFERENCES subjects(id) ON DELETE RESTRICT,
  term_id uuid NOT NULL REFERENCES terms(id) ON DELETE RESTRICT,
  assessment_date date NOT NULL,
  grade_value numeric(6,2) NOT NULL,
  grading_scale text NULL,
  notes text NULL,
  created_by_tutor_id uuid NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS assessment_scope_tags (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  real_grade_id uuid NOT NULL REFERENCES real_grades(id) ON DELETE CASCADE,
  topic_id uuid NULL REFERENCES topics(id) ON DELETE SET NULL,
  microconcept_id uuid NULL REFERENCES microconcepts(id) ON DELETE SET NULL,
  weight numeric(6,4) NULL
);

-- ============================================================
-- AUDIT LOG
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_logs (
  id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
  actor_user_id uuid NULL REFERENCES users(id) ON DELETE SET NULL,
  action_code text NOT NULL,
  entity_type text NOT NULL,
  entity_id uuid NULL,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now()
);

-- ============================================================
-- Updated_at trigger helper (opcional)
-- ============================================================

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  -- users
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_users_updated_at') THEN
    CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- tutors
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_tutors_updated_at') THEN
    CREATE TRIGGER trg_tutors_updated_at
    BEFORE UPDATE ON tutors
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- students
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_students_updated_at') THEN
    CREATE TRIGGER trg_students_updated_at
    BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- subjects
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_subjects_updated_at') THEN
    CREATE TRIGGER trg_subjects_updated_at
    BEFORE UPDATE ON subjects
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- terms
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_terms_updated_at') THEN
    CREATE TRIGGER trg_terms_updated_at
    BEFORE UPDATE ON terms
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- topics
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_topics_updated_at') THEN
    CREATE TRIGGER trg_topics_updated_at
    BEFORE UPDATE ON topics
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- microconcepts
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_microconcepts_updated_at') THEN
    CREATE TRIGGER trg_microconcepts_updated_at
    BEFORE UPDATE ON microconcepts
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- knowledge_entries
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_knowledge_entries_updated_at') THEN
    CREATE TRIGGER trg_knowledge_entries_updated_at
    BEFORE UPDATE ON knowledge_entries
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- items
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_items_updated_at') THEN
    CREATE TRIGGER trg_items_updated_at
    BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;

  -- student_context
  IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trg_student_context_updated_at') THEN
    CREATE TRIGGER trg_student_context_updated_at
    BEFORE UPDATE ON student_context
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
  END IF;
END $$;

-- ============================================================
-- Seed mínimo recomendado (roles, activity types)
-- ============================================================

INSERT INTO roles (code, name)
VALUES
  ('PLAYER','Alumno'),
  ('TUTOR','Tutor'),
  ('ADMIN','Administrador')
ON CONFLICT (code) DO NOTHING;

INSERT INTO activity_types (code, name)
VALUES
  ('QUIZ','Quiz'),
  ('MATCH','Emparejar'),
  ('CLOZE','Completar huecos'),
  ('REVIEW','Repaso'),
  ('EXAM_STYLE','Tipo examen')
ON CONFLICT (code) DO NOTHING;

-- Nota: recommendation_catalog se carga desde el Documento 05 (R01-R40)
-- ============================================================
```

---

## 3. Notas de implementación y evolución

### 3.1 Tabla `student_context`

En V1 se modela como:

* `term_id` único por alumno
* `subject_ids` como array

En V2 puede normalizarse con tabla N:N `student_subjects`.

### 3.2 `learning_events` append-only

Clave para recalcular métricas:

* No actualizar, no borrar (salvo cumplimiento/retención).
* Cualquier corrección se hace con un evento nuevo.

### 3.3 Versionado

* `metrics_version`, `catalog_version`, `engine_version`, `ruleset_version` permiten auditoría total.

### 3.4 Índices

Se incluyen índices mínimos para:

* eventos por alumno y tiempo
* agregados por ámbito
* recomendaciones activas por alumno

---

## 4. Carga del catálogo de recomendaciones (R01–R40)

Este documento no inserta las 40 recomendaciones para no duplicar contenido.
El catálogo se debe poblar a partir del Documento 05 y versionarse como seed.

---

## 5. Criterio de completitud para Sprint 0

Sprint 0 puede darse por cerrado cuando:

* El DDL se aplica sin errores.
* Se pueden crear usuarios, alumnos y tutores.
* Se pueden insertar eventos en `learning_events`.
* Se pueden consultar por alumno ordenados por tiempo.
