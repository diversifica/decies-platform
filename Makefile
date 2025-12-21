.PHONY: help dev-up dev-down dev-restart db-reset test lint lint-fix install clean export-llm-schemas

# Variables
DOCKER_COMPOSE = docker compose -f docker-compose.dev.yml
BACKEND_DIR = backend
FRONTEND_DIR = frontend

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev-up: ## Inicia entorno dev con Docker
	$(DOCKER_COMPOSE) up -d
	@echo "✅ DECIES dev environment running"
	@echo "Backend: http://localhost:8000/docs"
	@echo "Frontend: http://localhost:3000"

dev-down: ## Detiene entorno dev
	$(DOCKER_COMPOSE) down

dev-restart: ## Reinicia entorno dev
	$(DOCKER_COMPOSE) restart

dev-logs: ## Muestra logs del entorno dev
	$(DOCKER_COMPOSE) logs -f

db-reset: ## Resetea la base de datos
	$(DOCKER_COMPOSE) down -v
	$(DOCKER_COMPOSE) up -d db
	@echo "⏳ Esperando PostgreSQL..."
	@sleep 5
	cd $(BACKEND_DIR) && alembic upgrade head
	@echo "✅ Database reset complete"

install: ## Instala dependencias backend y frontend
	cd $(BACKEND_DIR) && uv sync
	cd $(FRONTEND_DIR) && npm install
	@echo "✅ Dependencies installed"

test: ## Ejecuta todos los tests
	@echo "Testing backend..."
	cd $(BACKEND_DIR) && pytest
	@echo "Testing frontend..."
	cd $(FRONTEND_DIR) && npm run test
	@echo "✅ All tests passed"

lint: ## Ejecuta linters
	@echo "Linting backend..."
	cd $(BACKEND_DIR) && ruff check .
	@echo "Linting frontend..."
	cd $(FRONTEND_DIR) && npm run lint

lint-fix: ## Ejecuta linters con auto-fix
	cd $(BACKEND_DIR) && ruff check --fix .
	cd $(FRONTEND_DIR) && npm run lint -- --fix

migration: ## Crea nueva migración Alembic
	@read -p "Migration message: " msg; \
	cd $(BACKEND_DIR) && alembic revision --autogenerate -m "$$msg"

export-openapi: ## Exporta especificación OpenAPI
	cd $(BACKEND_DIR) && python -c "from app.main import app; import json; print(json.dumps(app.openapi()))" > ../docs/openapi.json
	@echo "✅ OpenAPI spec exported to docs/openapi.json"

export-llm-schemas: ## Exporta schemas LLM a docs/llm_schemas
	python scripts/export-llm-schemas.py
	@echo "✅ LLM schemas exported to docs/llm_schemas"

clean: ## Limpia archivos temporales
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	cd $(FRONTEND_DIR) && rm -rf .next
	@echo "✅ Cleaned temporary files"
