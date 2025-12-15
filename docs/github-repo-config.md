# GitHub Repository Configuration Guide

## Protección de Branches (Branch Protection Rules)

### Para configurar `main` (Producción)

1. Ve a **Settings** > **Branches** > **Add branch protection rule**

2. **Branch name pattern:** `main`

3. **Configuración recomendada:**

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: 1
   - ✅ Dismiss stale pull request approvals when new commits are pushed
   - ✅ Require review from Code Owners

   ✅ **Require status checks to pass before merging**
   - ✅ Require branches to be up to date before merging
   - Status checks requeridos:
     - `test (backend-ci.yml)`
     - `test (frontend-ci.yml)`

   ✅ **Require conversation resolution before merging**

   ✅ **Do not allow bypassing the above settings**

   ✅ **Restrict who can push to matching branches**
   - Excepciones: Solo administradores

   ❌ Allow force pushes: **Disabled**
   ❌ Allow deletions: **Disabled**

### Para configurar `develop` (Integración Continua)

1. **Branch name pattern:** `develop`

2. **Configuración recomendada:**

   ✅ **Require a pull request before merging**
   - ✅ Require approvals: 1 (opcional, puedes ser más flexible)
   
   ✅ **Require status checks to pass before merging**
   - Status checks requeridos:
     - `test (backend-ci.yml)`
     - `test (frontend-ci.yml)`

   ✅ **Require conversation resolution before merging**

   ❌ Allow force pushes: **Disabled** (aunque puedes habilitarlo si eres solo tú)
   ❌ Allow deletions: **Disabled**

---

## Configuración de Dependabot

Ya está configurado en `.github/dependabot.yml` ✅

Para habilitar Dependabot alerts:

1. **Settings** > **Security** > **Code security and analysis**
2. Habilitar:
   - ✅ Dependabot alerts
   - ✅ Dependabot security updates 
   - ✅ Dependabot version updates

---

## Configuración de Secrets

### Secrets del Repositorio

**Settings** > **Secrets and variables** > **Actions**

Añadir secrets necesarios para CI/CD:

```
OPENAI_API_KEY           # Para tests que requieran LLM
DATABASE_URL_TEST        # Si necesitas DB de test en CI
```

### Secrets para Deployment (cuando sea necesario)

```
EASYPANEL_BACKEND_WEBHOOK_URL
EASYPANEL_FRONTEND_WEBHOOK_URL
```

---

## Labels Recomendados

**Settings** > **Labels** - Crear si no existen:

### Por Tipo
- `bug` (rojo) - Algo no funciona
- `enhancement` (verde) - Nueva funcionalidad
- `documentation` (azul) - Mejoras en documentación
- `refactor` (amarillo) - Mejora de código sin cambio funcional
- `security` (rojo oscuro) - Vulnerabilidad o hardening
- `performance` (naranja) - Mejora de rendimiento

### Por Componente
- `backend` (púrpura)
- `frontend` (cyan)
- `ci` (gris)
- `dependencies` (gris claro)

### Por Estado
- `wip` (amarillo) - Work in Progress
- `blocked` (rojo) - Bloqueado esperando algo
- `ready-for-review` (verde claro)
- `needs-discussion` (azul claro)

### Por Prioridad
- `priority:critical` (rojo)
- `priority:high` (naranja)
- `priority:medium` (amarillo)
- `priority:low` (verde)

---

## Configurar GitHub Pages (Opcional)

Si quieres hospedar la documentación públicamente:

1. **Settings** > **Pages**
2. **Source:** Deploy from a branch
3. **Branch:** `main` > `/docs`
4. **Save**

Documentación estará en: `https://diversifica.github.io/decies-platform/`

---

## Webhooks para Deployment (Cuando sea necesario)

**Settings** > **Webhooks** > **Add webhook**

### Para Easypanel (Backend)
```
Payload URL: [Tu URL de Easypanel Backend]
Content type: application/json
Events: Just the push event
Active: ✅
```

### Para Easypanel (Frontend)  
```
Payload URL: [Tu URL de Easypanel Frontend]
Content type: application/json
Events: Just the push event
Active: ✅
```

---

## Primer Release Tag (Cuando completes Sprint 0)

```bash
# En develop, cuando esté todo funcionando
git checkout develop
git pull origin develop

# Crear tag
git tag -a v0.1.0 -m "Sprint 0 complete - Basic infrastructure functional"

# Push tag
git push origin v0.1.0
```

Luego en GitHub:
1. **Releases** > **Create a new release**
2. **Tag:** v0.1.0
3. **Release title:** "v0.1.0 - Sprint 0 Complete"
4. **Description:** Resumen de lo completado en Sprint 0
5. **Publish release**

---

## Checklist de Configuración Completa

- [ ] Protección de branch `main`
- [ ] Protección de branch `develop`
- [ ] Dependabot habilitado (alerts + updates)
- [ ] Labels creados
- [ ] Secrets configurados (cuando sea necesario)
- [ ] CODEOWNERS verificado
- [ ] GitHub Pages (opcional)
- [ ] Webhooks deployment (cuando sea necesario)
- [ ] Primer release tag cuando completes Sprint 0
