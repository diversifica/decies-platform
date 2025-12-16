param(
[switch]$Build = $true
)

$ErrorActionPreference = "Stop"

Write-Host "Levantando stack dev con Docker Compose..."

$composeFile = "docker-compose.dev.yml"

if ($Build) {
docker compose -f $composeFile up -d --build
} else {
docker compose -f $composeFile up -d
}

Write-Host "Estado de contenedores:"
docker ps
