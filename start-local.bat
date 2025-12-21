@echo off
setlocal

set "ROOT=%~dp0"
pushd "%ROOT%"

echo [1/5] Ensure env files
if not exist ".env" if exist ".env.example" copy ".env.example" ".env" >nul
if not exist "backend\.env" if exist "backend\.env.example" copy "backend\.env.example" "backend\.env" >nul
if not exist "frontend\.env" if exist "frontend\.env.example" copy "frontend\.env.example" "frontend\.env" >nul

echo [2/5] Start docker services
docker compose -f docker-compose.dev.yml up -d --build
if errorlevel 1 goto :error

echo [3/5] Run migrations
powershell -ExecutionPolicy Bypass -File .\scripts\ps\db-migrate.ps1
if errorlevel 1 goto :error

echo [4/5] Seed sample data
powershell -ExecutionPolicy Bypass -File .\scripts\ps\db-seed.ps1
if errorlevel 1 goto :error

echo [5/5] Start frontend dev server
pushd "frontend"
if not exist "node_modules\.bin\next" (
    call npm install
    if errorlevel 1 goto :error
)
start "DECIES Frontend" cmd /c "npm run dev -- -p 3000"
popd

echo.
echo Ready:
echo - Frontend: http://localhost:3000
echo - Backend:  http://localhost:8000/docs
echo.
popd
exit /b 0

:error
echo.
echo Error: startup failed. Check output above.
popd
exit /b 1
