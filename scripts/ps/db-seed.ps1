$ErrorActionPreference = "Stop"

Write-Host "Ejecutando seed (backend/seed.py) en contenedor..."

$composeFile = "docker-compose.dev.yml"

# Asegura backend arriba (para tener herramientas disponibles en el contenedor)
docker compose -f $composeFile up -d backend

# Ejecuta seed
docker compose -f $composeFile exec -T backend sh -lc "python seed.py"

Write-Host "OK"
