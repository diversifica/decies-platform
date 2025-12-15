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
- 🎨 Frontend: http://localhost:3000
- 🔧 Backend API: http://localhost:8000/docs
- 🗄️ Database: localhost:5432

## 📋 Comandos Principales

```bash
make help          # Ver todos los comandos disponibles
make dev-up        # Iniciar entorno de desarrollo
make dev-down      # Detener servicios
make test          # Ejecutar tests
make lint          # Ejecutar linters
make db-reset      # Resetear base de datos
```

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
