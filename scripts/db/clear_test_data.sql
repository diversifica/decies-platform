-- Script para limpiar datos de prueba en la base de datos DECIES.
-- No borra tablas maestras (roles, activity_types, recommendation_catalog),
-- pero resetea el resto con TRUNCATE + RESTART IDENTITY para dejar el esquema listo.
--
-- Uso desde el backend (p.ej. con psql en el contenedor de Postgres):
--   docker compose -f docker-compose.dev.yml exec db psql -U decies -d decies -f /workspace/scripts/db/clear_test_data.sql

BEGIN;
TRUNCATE TABLE
  activity_sessions,
  activity_session_items,
  learning_events,
  content_uploads,
  real_grades,
  assessment_scope_tags,
  items,
  knowledge_entries,
  knowledge_chunks,
  llm_runs,
  metric_aggregates,
  mastery_states,
  microconcepts,
  microconcept_prerequisites,
  tutor_reports,
  tutor_report_sections,
  students,
  subjects,
  academic_years,
  terms,
  topics,
  tutors,
  users,
  recommendation_instances,
  recommendation_evidence,
  tutor_decisions,
  recommendation_outcomes
RESTART IDENTITY CASCADE;
COMMIT;
