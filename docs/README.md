# Documentación DECIES Platform

Bienvenido a la documentación técnica y de producto de **DECIES** (sistema de análisis y recomendaciones pedagógicas adaptativas).

## 📚 Índice de Documentación

### 00 - Fundación
- [00 - The DECIES Principle](00_fundacion/00_The_DECIES_Principle_V1.md)
- [00A - Índice de Documentación](00_fundacion/00A_Indice_Documentacion_DECIES.md)

### 01 - Modelo Pedagógico
- Fundamentos del modelo adaptativo
- Criterios de evaluación

### 02 - Diseño del Sistema
- Arquitectura de eventos
- Motor de métricas
- Motor de recomendaciones

### 03 - Planificación
- Roadmap y sprints
- Milestone tracking

### 04 - Stack Técnico
- [16 - Stack Técnico Concreto y Tareas Ejecutables](04_stack_tecnico/16_Stack_Tecnico_Concreto_y_Tareas_Ejecutables_V1.md)

### 05 - Calidad
- Testing strategy
- CI/CD pipeline

### 06 - Sprints
- Sprint planning
- Sprint retrospectives

### 07 - Gobierno
- Decisiones técnicas
- ADRs (Architecture Decision Records)

### Prompts LLM
- [Backend Agent](prompts/backend-agent.md)
- [Frontend Agent](prompts/frontend-agent.md)

---

## 🚀 Quick Start para Agentes LLM

Si eres un agente LLM trabajando en este proyecto, **este es tu punto de entrada**:

### 1️⃣ Contexto Fundamental
Primero, entiende los principios del proyecto:
- 📘 [00 - The DECIES Principle](00_fundacion/00_The_DECIES_Principle_V1.md) - Fundamento filosófico y educativo del sistema
- 📋 [00A - Índice de Documentación](00_fundacion/00A_Indice_Documentacion_DECIES.md) - Navegación completa

### 2️⃣ Tu Rol Específico
Lee el prompt correspondiente a tu área de trabajo:
- 🐍 **Backend:** [prompts/backend-agent.md](prompts/backend-agent.md)
  - FastAPI + PostgreSQL + SQLAlchemy
  - Arquitectura de servicios (events, metrics, recommendations, llm)
  - Testing con Pytest, linting con Ruff
- ⚛️ **Frontend:** [prompts/frontend-agent.md](prompts/frontend-agent.md)
  - Next.js 14 (App Router) + TypeScript
  - Dominios (tutor) y (student)
  - Testing con Vitest + Testing Library

### 3️⃣ Arquitectura Técnica
Entiende el stack y decisiones técnicas:
- 🏗️ [04 - Stack Técnico Concreto](04_stack_tecnico/16_Stack_Tecnico_Concreto_y_Tareas_Ejecutables_V1.md)
  - Tecnologías elegidas y justificación
  - Sprint 0 y Sprint 1 desglosados
  - Decisiones técnicas explícitas

### 4️⃣ Flujo de Trabajo
Consulta las guías de contribución:
- 🤝 [CONTRIBUTING.md](../CONTRIBUTING.md) - Conventional Commits, flujo Git, seguridad
- 🛠️ [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) - Setup local, arquitectura, debugging

---

## 📝 Reglas para Mantener Docs

**Contrato de documentación:**

1. ✅ **Todo cambio de arquitectura** requiere PR que actualice docs/
2. ✅ **Nuevas métricas o reglas** deben documentarse en 02_diseno_sistema/
3. ✅ **Decisiones técnicas importantes** van a 07_gobierno/ (ADRs)
4. ✅ **Sprint completado** implica actualizar 06_sprints/ con retrospectiva
5. ❌ **NO documentar** implementación interna (eso va en docstrings/comentarios)

**Formato:**
- Usa Markdown estándar
- Enlaces relativos para navegación interna
- Código con syntax highlighting apropiado
- Diagramas Mermaid cuando ayude a clarificar
