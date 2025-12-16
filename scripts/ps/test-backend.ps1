$ErrorActionPreference = "Stop"

Write-Host "Tests backend (pytest) en contenedor..."

$composeFile = "docker-compose.dev.yml"

docker compose -f $composeFile up -d backend

docker compose -f $composeFile exec -T backend sh -lc "python -m pip install -e '.[dev]'"

docker compose -f $composeFile exec -T backend pytest -q

Write-Host "OK"
