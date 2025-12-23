from __future__ import annotations

import json
import sys
from pathlib import Path

script_path = Path(__file__).resolve()
backend_root = script_path.parents[1]
project_root = backend_root.parents[1]
sys.path.append(str(backend_root))

from app.main import app


def main() -> None:
    output_file = project_root / "docs" / "openapi.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    openapi = app.openapi()
    output_file.write_text(json.dumps(openapi, ensure_ascii=False))


if __name__ == "__main__":
    main()
