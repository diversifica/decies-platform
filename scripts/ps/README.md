# Scripts PowerShell (Windows)

Estos scripts proporcionan equivalentes a los objetivos habituales del Makefile para desarrollo en Windows.

## Uso

Desde la raíz del repositorio:

* Levantar entorno:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\dev-up.ps1
  ```

* Parar entorno:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\dev-down.ps1
  ```

* Lint backend (en contenedor):

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\lint-backend.ps1
  ```

* Tests backend (en contenedor):

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\test-backend.ps1
  ```

* Migraciones (alembic) en contenedor:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\db-migrate.ps1
  ```

* Seed (datos de ejemplo) en contenedor:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\db-seed.ps1
  ```

* Exportar schemas LLM:

  ```powershell
  powershell -ExecutionPolicy Bypass -File .\scripts\ps\export-llm-schemas.ps1
  ```

## Credenciales seed (dev)

* Tutor: `tutor@decies.com` / `decies`
* Estudiante: `student@decies.com` / `decies`

## Notas

* Los comandos de lint y test se ejecutan dentro del contenedor `backend` para evitar dependencias locales (por ejemplo, diferencias de Python/Conda en Windows).
* Si actualizas el repo y aparecen errores de base de datos (tablas faltantes), ejecuta `db-migrate.ps1`.
* Si no puedes iniciar sesión tras actualizar el repo, ejecuta `db-seed.ps1` (los hashes de contraseña se recalculan al reseedear).
