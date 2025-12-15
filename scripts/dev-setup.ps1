# PowerShell version of dev-setup.sh for Windows users
Write-Host "🚀 Setting up DECIES development environment..." -ForegroundColor Green

# Copy env files
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✅ Created .env" -ForegroundColor Green
}

if (-not (Test-Path "backend\.env")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "✅ Created backend\.env" -ForegroundColor Green
}

if (-not (Test-Path "frontend\.env")) {
    Copy-Item "frontend\.env.example" "frontend\.env"
    Write-Host "✅ Created frontend\.env" -ForegroundColor Green
}

# Install dependencies
Write-Host "📦 Installing dependencies..." -ForegroundColor Cyan
make install

# Start Docker
Write-Host "🐳 Starting Docker services..." -ForegroundColor Cyan
make dev-up

Write-Host ""
Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host "Backend: http://localhost:8000/docs"
Write-Host "Frontend: http://localhost:3000"
