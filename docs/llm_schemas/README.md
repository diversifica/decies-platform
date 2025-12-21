# LLM JSON Schemas

Este directorio contiene los JSON Schemas de salida para las etapas E2/E3/E4/E5.
Se generan desde modelos Pydantic en `backend/app/services/llm_service.py`.

Generacion:

```bash
python scripts/export-llm-schemas.py
```

Validacion:

```bash
cd backend
pytest -q tests/test_llm_schema_contracts.py
```
