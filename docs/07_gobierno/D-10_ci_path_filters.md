# D-10 – Path Filters en CI Workflows (Monorepo)

## Contexto

Sprint 0 - Day 1: Al crear el primer PR, el CI de backend ejecutaba incluso cuando solo se modificaban archivos de documentación, causando fallos innecesarios.

## Problema Detectado

**Síntoma en PR #1:**
```
All checks have failed
Backend CI / test (pull_request) - Failing after 10s
```

**Causa raíz:**
Los workflows `.github/workflows/backend-ci.yml` y `frontend-ci.yml` se ejecutaban en **todos los PRs**, sin importar qué archivos cambiaban.

Resultado:
- PR de docs (`docs/07_gobierno/D-09...`) → Ejecuta backend CI
- Backend CI falla (no hay tests aún, o pytest exit 5)
- PR bloqueado innecesariamente

## Decisión

**Usar `paths:` filter en workflows para ejecutar solo cuando cambian archivos relevantes.**

### Workflow Backend
```yaml
on:
  pull_request:
    paths:
      - "backend/**"
      - ".github/workflows/backend-ci.yml"
  push:
    branches: [main, develop]
    paths:
      - "backend/**"
      - ".github/workflows/backend-ci.yml"
```

### Workflow Frontend
```yaml
on:
  pull_request:
    paths:
      - "frontend/**"
      - ".github/workflows/frontend-ci.yml"
  push:
    branches: [main, develop]
    paths:
      - "frontend/**"
      - ".github/workflows/frontend-ci.yml"
```

## Rationale

1. **Eficiencia:** No ejecutar CI innecesariamente (ahorra runners GitHub Actions)
2. **Claridad:** Si cambias docs, no deberías ver fallos de backend CI
3. **Monorepo estándar:** Práctica común en monorepos (Nx, Turborepo, etc.)
4. **Self-update:** Incluir el propio workflow en `paths:` permite que cambios al CI se prueben

## Alternativas Consideradas

1. ❌ **Sin filtros (ejecutar siempre)**
   - Pro: Detecta dependencias ocultas
   - Contra: Ruido innecesario, desperdicia CI minutes

2. ✅ **Path filters** (ELEGIDA)
   - Pro: Ejecuta solo cuando relevante
   - Pro: Estándar en monorepos
   - Contra: Requiere mantener paths actualizados

3. ❌ **Workflow único con matrix**
   - Pro: Un solo archivo
   - Contra: Más complejo, menos granular

## Implementación

**Triggers:**
- PR que cambia `backend/**` → Ejecuta backend CI ✅
- PR que cambia `frontend/**` → Ejecuta frontend CI ✅
- PR que cambia `docs/**` → No ejecuta ninguno ✅
- PR que cambia `.github/workflows/backend-ci.yml` → Ejecuta backend CI ✅

**Casos especiales:**
- Cambios en raíz (Makefile, docker-compose.dev.yml) → No ejecutan CI
- Cambios en workflows → Ejecutan su propio CI (self-test)

## Validación

```bash
# PR solo con docs (como D-09)
git checkout -b test/docs-only
echo "test" >> docs/README.md
git commit -m "docs: test"
git push
# Resultado esperado: Ningún CI ejecuta ✅

# PR con backend
git checkout -b test/backend-change
echo "test" >> backend/app/main.py
git commit -m "feat: test"
git push
# Resultado esperado: Solo backend CI ejecuta ✅
```

## Mejoras Futuras

Si en el futuro necesitas ejecutar CI en cambios de configuración global:

```yaml
on:
  pull_request:
    paths:
      - "backend/**"
      - "docker-compose*.yml"  # Cambios en compose afectan backend
      - "Makefile"              # Cambios en Makefile pueden afectar
      - ".github/workflows/backend-ci.yml"
```

## Estado

**ABIERTA** - Implementado en commit `ci: add path filters to workflows`

Monitorear durante Sprint 0-1 para ajustar si es necesario.

## Referencias

- PR #1: https://github.com/diversifica/decies-platform/pull/1
- GitHub Docs: [Workflow syntax - paths](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore)
- Equivalente en otros monorepos: Nx affected, Turborepo filter

## Fecha

2025-12-15
