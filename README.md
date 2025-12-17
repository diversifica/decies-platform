# 🎓 DECIES Platform

**Sistema de análisis y recomendaciones pedagógicas adaptativas** para educación personalizada basada en eventos de aprendizaje.

## 🚀 Inicio Rápido

```bash
# Instalación automática (Linux/macOS)
./scripts/dev-setup.sh

# O en Windows (PowerShell)
.\scripts\dev-setup.ps1

# O manual
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
make install
make dev-up
```

**URLs:**

- 🎨 Frontend: <http://localhost:3000>
- 🔧 Backend API: <http://localhost:8000/docs>
- 🗄️ Database: localhost:5432

## Inicio rápido (desarrollo local)

### Requisitos

- Docker Desktop (con `docker compose`)
- Git

### Levantar el entorno (Docker)

#### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ps\dev-up.ps1
```

Parar:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ps\dev-down.ps1
```

Lint backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ps\lint-backend.ps1
```

Tests backend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\ps\test-backend.ps1
```

#### Linux/Mac

```bash
make dev-up
```

Parar:

```bash
make dev-down
```

Lint backend:

```bash
make lint-backend
```

Tests backend:

```bash
make test-backend
```

### Healthchecks

- Backend: `GET http://localhost:8000/health`
- DB: `GET http://localhost:8000/health/db`

## 🏗️ Stack Tecnológico

### Backend

- **Python 3.12** + **FastAPI**
- **PostgreSQL 15** + SQLAlchemy 2.x + Alembic
- **LLM Integration:** LangChain + OpenAI/Gemini
- **Testing:** Pytest + pytest-cov

### Frontend  

- **Next.js 14** (App Router)
- **React 18** + TypeScript
- **React Query** para estado del servidor
- **Testing:** Vitest + Testing Library

### Infraestructura

- **Docker** + Docker Compose
- **GitHub Actions** (CI/CD)
- **uv/Poetry** para gestión de dependencias Python

## 📂 Estructura del Proyecto

Ver [docs/README.md](docs/README.md) para documentación completa.

```
decies-platform/
├── backend/          # FastAPI + PostgreSQL
├── frontend/         # Next.js + React  
├── docs/             # Documentación navegable (00-24)
├── scripts/          # Utilidades del monorepo
├── Makefile          # Comandos profesionales
└── docker-compose*   # Orquestación Docker
```

## 🧭 Arquitectura

**DECIES** implementa una arquitectura basada en eventos:

1. **Event Service:** Captura eventos de aprendizaje (append-only)
2. **Metric Engine:** Procesa eventos y calcula métricas agregadas
3. **Recommendation Engine:** Aplica reglas y genera recomendaciones explicables
4. **LLM Pipeline:** Extrae, estructura y genera contenido educativo

Ver [docs/02_diseno_sistema/](docs/02_diseno_sistema/) para detalles completos.

## 🤝 Contribuir

Consulta [CONTRIBUTING.md](CONTRIBUTING.md) para flujo de trabajo, estándares de código y proceso de review.

## 📄 Licencia

MIT © Diversifica
