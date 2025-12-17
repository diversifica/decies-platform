$ErrorActionPreference = "Stop"

Write-Host "Aplicando migraciones (alembic) en contenedor..."

$composeFile = "docker-compose.dev.yml"

# Asegura backend arriba (para tener herramientas disponibles en el contenedor)
docker compose -f $composeFile up -d backend

# Instala dependencias dev (incluye alembic)
docker compose -f $composeFile exec -T backend sh -lc "python -m pip install -e '.[dev]'"

# Ejecuta migraciones a HEAD
docker compose -f $composeFile exec -T backend sh -lc "python -m alembic upgrade head"

Write-Host "OK"
