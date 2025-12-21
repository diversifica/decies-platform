# Documento 21 - Checklist Preproduccion (V1)

## Objetivo

Dejar el sistema listo para pruebas preproduccion y paso a produccion
con evidencia reproducible.

## 1) Estado del repo

- [ ] CI en verde en `develop` (backend + frontend).
- [ ] Sin cambios locales sin commitear.
- [ ] PRs pendientes cerrados o mergeados.

## 2) Contrato API (OpenAPI)

- [ ] `make export-openapi` genera `docs/openapi.json`.
- [ ] `pytest -q tests/test_openapi_contract.py` pasa.
- [ ] Revisar que endpoints criticos existan:
  - `/api/v1/auth/me`
  - `/api/v1/activities/sessions`
  - `/api/v1/recommendations/students/{student_id}`
  - `/api/v1/reports/students/{student_id}/generate`

## 3) Contratos LLM (JSON Schemas)

- [ ] `python scripts/export-llm-schemas.py` genera schemas en `docs/llm_schemas`.
- [ ] `pytest -q tests/test_llm_schema_contracts.py` pasa.
- [ ] Validar que E2/E3/E4/E5 tienen schema versionado.

## 4) Datasets de regresion (DS-01..DS-05)

- [ ] Archivos en `docs/testing/datasets/`.
- [ ] Contenido revisado (sin datos personales).
- [ ] Registro de cambios si se actualiza un dataset.

## 5) E2E (flujos criticos)

- [ ] E2E-01: `pytest -q tests/e2e/test_e2e_01_flow.py`
- [ ] E2E-02: `pytest -q tests/e2e/test_e2e_02_flow.py`
- [ ] E2E-03: `pytest -q tests/e2e/test_e2e_03_prereq_r05_cloze.py`
- [ ] E2E-04: `pytest -q tests/e2e/test_e2e_04_outcomes_report.py`
- [ ] E2E-05: `pytest -q tests/e2e/test_e2e_05_review_schedule.py`
- [ ] E2E-06: `pytest -q tests/e2e/test_e2e_06_external_validation_report.py`

## 6) Seguridad y privacidad

- [ ] Revisar que no hay secretos en el repo (`.env` fuera de git).
- [ ] Confirmar que los logs no contienen datos personales.
- [ ] Revalidar RBAC en endpoints criticos (tutor vs student vs admin).

## 7) Release

- [ ] Tag de release creado (ej: `v0.1.0` o `v1.0.0`).
- [ ] Changelog/Notas de release actualizadas.
- [ ] Evidencia de ejecucion de la checklist.
