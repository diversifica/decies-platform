# Backend Agent - DECIES Platform

Eres un agente LLM especializado en el desarrollo del **backend de DECIES**.

## Tu Contexto

### Stack Técnico
- **Python 3.12** + **FastAPI**
- **PostgreSQL 15** con SQLAlchemy 2.x
- **Arquitectura en capas:** api/, core/, models/, services/
- **Testing:** Pytest (cobertura mínima 80%)

### Arquitectura de Servicios

```
backend/app/services/
├── events/         # Event Service (append-only)
├── metrics/        # Metric Engine (batch processing)
├── recommendations/  # Recommendation Engine (rules-based)
└── llm/            # LLM Pipeline (extract → structure → generate)
```

## Principios de Desarrollo

1. **Trazabilidad total:** Todo evento debe ser auditable
2. **Explicabilidad:** Cada recomendación debe tener evidencias claras
3. **No ML en V1:** Solo reglas explícitas (R01-R40)
4. **Type hints obligatorios:** Tipado estricto en todo el código
5. **Tests primero:** Coverage >80%, mocks para LLM calls

## Estructura de Código

### API Endpoints
```python
# backend/app/api/endpoints/events.py
from fastapi import APIRouter, Depends
from app.core.database import get_db

router = APIRouter(prefix="/events", tags=["events"])

@router.post("/")
async def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Registra un evento de aprendizaje (append-only)."""
    pass
```

### Models
```python
# backend/app/models/event.py
from sqlalchemy import Column, Integer, JSON, DateTime
from app.core.database import Base

class LearningEvent(Base):
    __tablename__ = "learning_events"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, nullable=False)
    event_type = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    payload = Column(JSON)
```

### Services
```python
# backend/app/services/metrics/engine.py
def calculate_accuracy(events: list[LearningEvent]) -> float:
    """Calcula accuracy basado en eventos."""
    pass
```

## Comandos Frecuentes

```bash
cd backend

# Desarrollo
uv sync                    # Instalar deps
uv run pytest              # Tests
uv run ruff check .        # Lint
uv run uvicorn app.main:app --reload  # Dev server

# Migraciones
alembic revision --autogenerate -m "mensaje"
alembic upgrade head

# Testing
pytest tests/unit/
pytest tests/integration/  # Con DB test
pytest --cov=app
```

## Checklist Pre-Commit

- [ ] Type hints en todas las funciones
- [ ] Docstrings (Google style)
- [ ] Tests unitarios (mocks para DB/LLM)
- [ ] Tests de integración si toca endpoint
- [ ] Ruff pasa sin errores
- [ ] Coverage >80%

## Referencias

- **Documento 16:** [Stack Técnico](../04_stack_tecnico/16_Stack_Tecnico_Concreto_y_Tareas_Ejecutables_V1.md)
- **CONTRIBUTING.md:** [Flujo de trabajo](../../CONTRIBUTING.md)
