# D-12 — Estrategia de ramas (`main` / `develop`)

## Contexto

El repositorio usa dos ramas principales:

- `develop`: integración continua de trabajo (features/fixes).
- `main`: rama por defecto y base estable.

Con el tiempo puede aparecer *drift* (diferencias grandes entre ramas), lo que:

- rompe PRs automáticos (p.ej. Dependabot apuntando a una base desalineada),
- dificulta mantener `main` verde,
- complica aplicar fixes de seguridad en la rama por defecto.

## Decisión

1. **La rama por defecto se mantiene como `main`.**
2. **Toda feature/fix se integra en `develop` vía PR** (base `develop`), siguiendo `CONTRIBUTING.md`.
3. **Cadencia de “release sync”**:
   - Abrir PR periódico `develop -> main` (merge commit recomendado).
   - Objetivo: mantener `main` cerca de `develop` y en verde.
4. **Fixes urgentes (hotfix/security)**:
   - Si un fix debe caer en `main` primero (p.ej. alertas de seguridad en rama por defecto), se backportea a `develop` con un PR `main -> develop` o cherry-pick.
5. **Dependabot (no security)**:
   - PRs de updates regulares targetean `develop` para respetar el flujo.

## Consecuencias

- `main` se mantiene como referencia estable y rama por defecto (alerts/seguridad).
- `develop` concentra el trabajo diario y reduce fricción de CI/PRs.
- Evitamos PRs rotos por incompatibilidades entre dependencias y “base” desalineada.

## Operativa mínima

Checklist para sync `develop -> main`:

1. CI verde en `develop`.
2. Crear PR `develop` -> `main` con título tipo `chore(release): sync develop into main`.
3. Merge (preferible merge commit) cuando CI esté verde.
4. Crear PR `main` -> `develop` si hubo commits directos a `main` (security/hotfix), para mantener ambas ramas alineadas.
