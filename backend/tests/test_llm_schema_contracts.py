import json
from pathlib import Path

from app.services.llm_service import (
    E3MapResult,
    E5ValidationResult,
    ItemResult,
    StructureResult,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_schema(name: str) -> dict:
    path = _repo_root() / "docs" / "llm_schemas" / name
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize(schema: dict) -> str:
    return json.dumps(schema, sort_keys=True)


def test_llm_schema_e2_matches_model():
    actual = _normalize(_load_schema("e2_structure.schema.json"))
    expected = _normalize(StructureResult.model_json_schema())
    assert actual == expected


def test_llm_schema_e3_matches_model():
    actual = _normalize(_load_schema("e3_mapping.schema.json"))
    expected = _normalize(E3MapResult.model_json_schema())
    assert actual == expected


def test_llm_schema_e4_matches_model():
    actual = _normalize(_load_schema("e4_items.schema.json"))
    expected = _normalize(ItemResult.model_json_schema())
    assert actual == expected


def test_llm_schema_e5_matches_model():
    actual = _normalize(_load_schema("e5_validation.schema.json"))
    expected = _normalize(E5ValidationResult.model_json_schema())
    assert actual == expected
