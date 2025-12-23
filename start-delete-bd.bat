@echo off
setlocal

set "ROOT=%~dp0"
set "ROOT_DIR=%ROOT:~0,-1%"
pushd "%ROOT%"

echo [1/5] Ensure env files
if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul
if not exist "backend\.env" if exist "backend\.env.example" copy "backend\.env.example" "backend\.env" >nul
if not exist "frontend\.env" if exist "frontend\.env.example" copy "frontend\.env.example" "frontend\.env" >nul

echo [2/5] Start database ^& redis
docker compose -f docker-compose.dev.yml up -d db redis
if errorlevel 1 goto :error

echo [3/5] Limpiar datos existentes
docker compose -f docker-compose.dev.yml exec -T db psql -U decies -d decies -c "TRUNCATE TABLE activity_sessions,activity_session_items,learning_events,content_uploads,real_grades,assessment_scope_tags,items,knowledge_entries,knowledge_chunks,llm_runs,metric_aggregates,mastery_states,microconcepts,microconcept_prerequisites,tutor_reports,tutor_report_sections,students,subjects,academic_years,terms,topics,tutors,users,recommendation_instances,recommendation_evidence,tutor_decisions,recommendation_outcomes RESTART IDENTITY CASCADE;"
if errorlevel 1 goto :error

echo [4/5] Insertar datos base requeridos
docker compose -f docker-compose.dev.yml run --rm --volume "%ROOT_DIR%:/workspace" backend sh -c "PYTHONPATH=/workspace/backend python /workspace/scripts/db/seed_base.py"
if errorlevel 1 goto :error

echo [5/5] Levantar servicios completos
call start-local.bat
if errorlevel 1 goto :error

popd
exit /b 0

:error
echo.
echo Error: el proceso de limpieza falló. Revisa la salida anterior.
popd
exit /b 1
