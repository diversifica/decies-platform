import json
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.append(str(repo_root / "backend"))

    from app.services.llm_service import (  # noqa: WPS433
        E3MapResult,
        E5ValidationResult,
        ItemResult,
        StructureResult,
    )

    schemas = {
        "e2_structure.schema.json": StructureResult,
        "e3_mapping.schema.json": E3MapResult,
        "e4_items.schema.json": ItemResult,
        "e5_validation.schema.json": E5ValidationResult,
    }

    out_dir = repo_root / "docs" / "llm_schemas"
    out_dir.mkdir(parents=True, exist_ok=True)

    for filename, model in schemas.items():
        schema = model.model_json_schema()
        path = out_dir / filename
        path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
