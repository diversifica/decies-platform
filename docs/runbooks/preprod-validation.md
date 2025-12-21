# Runbook - Preprod validation

## Objetivo

Ejecutar la checklist preprod y dejar evidencia reproducible antes de produccion.

Checklist base: `docs/technical/05_calidad/21_Checklist_Preprod_V1.md`

## Pasos rapidos

1) OpenAPI

```bash
make export-openapi
cd backend
pytest -q tests/test_openapi_contract.py
```

2) Schemas LLM

```bash
python scripts/export-llm-schemas.py
cd backend
pytest -q tests/test_llm_schema_contracts.py
```

3) E2E

```bash
cd backend
pytest -q tests/e2e/test_e2e_01_flow.py
pytest -q tests/e2e/test_e2e_02_flow.py
pytest -q tests/e2e/test_e2e_03_prereq_r05_cloze.py
pytest -q tests/e2e/test_e2e_04_outcomes_report.py
pytest -q tests/e2e/test_e2e_05_review_schedule.py
pytest -q tests/e2e/test_e2e_06_external_validation_report.py
```

4) Dataset references

Revisar archivos en `docs/testing/datasets/`.
