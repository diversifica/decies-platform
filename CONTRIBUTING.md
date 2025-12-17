# Guía de Contribución - DECIES Platform

## Flujo de Trabajo Git

### 1. Branches

- `main`: Producción estable
- `develop`: Integración continua
- `feature/*`: Nuevas funcionalidades
- `fix/*`: Corrección de bugs
- `docs/*`: Actualizaciones de documentación

### 2. Seguridad y Secretos

**🔒 NUNCA subir secretos al repositorio.**

- ❌ NO COMMIT: `.env`, API keys, passwords, tokens, certificados
- ✅ USAR: `.env.example` con valores placeholder
- ✅ VERIFICAR: Antes de commit, revisar que no haya secretos con:
  ```bash
  git diff --staged | grep -i "api_key\|password\|secret\|token"
  ```

Si accidentalmente subes un secreto:
1. **Revocar el secreto inmediatamente**
2. Generar uno nuevo
3. Usar `git filter-branch` o contactar con el equipo

### 3. Crear Feature Branch

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-descriptivo
```

### 3. Conventional Commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: añade endpoint de recomendaciones
fix: corrige cálculo de métricas de mastery
docs: actualiza README con nuevos comandos
test: añade tests para Event Service
refactor: reorganiza estructura de services
chore: actualiza dependencias
```

### 4. Calidad Antes de Commit

```bash
# Backend
cd backend
ruff check .
pytest

# Frontend
cd frontend
npm run lint
npm run test

# O todo junto
make lint
make test
```

### 5. Pull Request

1. Push de la rama:
```bash
git push origin feature/nombre-descriptivo
```

2. Crear PR en GitHub:
   - Base: `develop`
   - Título: Conventional Commit format
   - Descripción: Explica QUÉ y POR QUÉ
   - Asignar reviewers

3. Esperar CI verde ✅
4. Esperar review y approval
5. Merge (squash and merge preferido)

## Estándares de Código

### Backend (Python)

- **Estilo:** Ruff (line-length 100)
- **Tipado:** Type hints obligatorios
- **Docstrings:** Google style
- **Testing:** Cobertura mínima 80%

### Frontend (TypeScript)

- **Estilo:** ESLint + Prettier
- **Tipado:** TypeScript estricto
- **Componentes:** Functional + Hooks
- **Testing:** Vitest para lógica, Testing Library para UI

## Testing Requirements

### Backend

- Tests unitarios para services
- Tests de integración para API endpoints
- Tests E2E para flujos críticos
- Mocks para LLM calls

### Frontend

- Tests de componentes UI
- Tests de hooks custom
- Tests de API client

## Code Review Process

### Como Autor

- [ ] CI pasa ✅
- [ ] Tests añadidos/actualizados
- [ ] Documentación actualizada si es necesario
- [ ] Sin console.log o prints de debug
- [ ] Cambios revisados personalmente

### Como Reviewer

- [ ] Código legible y mantenible
- [ ] Lógica correcta
- [ ] Tests adecuados
- [ ] Sin regresiones obvias
- [ ] Arquitectura respetada

## Comandos Útiles

```bash
make help          # Ver todos los comandos
make dev-up        # Entorno completo
make test          # Todos los tests
make lint          # Todos los linters
make lint-fix      # Auto-fix linting
make db-reset      # Reset DB + migraciones
```
