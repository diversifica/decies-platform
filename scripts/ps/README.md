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

## Notas

* Los comandos de lint y test se ejecutan dentro del contenedor `backend` para evitar dependencias locales (por ejemplo, diferencias de Python/Conda en Windows).
