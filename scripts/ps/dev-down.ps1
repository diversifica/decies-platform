$ErrorActionPreference = "Stop"

Write-Host "Parando stack dev..."
docker compose -f docker-compose.dev.yml down

Write-Host "OK"
