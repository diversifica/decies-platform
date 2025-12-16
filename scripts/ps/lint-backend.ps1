$ErrorActionPreference = "Stop"

Write-Host "Lint backend (ruff) en contenedor..."

$composeFile = "docker-compose.dev.yml"

docker compose -f $composeFile up -d backend

# Asegura deps dev instaladas
docker compose -f $composeFile exec -T backend sh -lc "python -m pip install -e '.[dev]'"

docker compose -f $composeFile exec -T backend ruff check .
docker compose -f $composeFile exec -T backend ruff format --check .

Write-Host "OK"
