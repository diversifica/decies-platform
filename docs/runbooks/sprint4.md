# Runbook — Sprint 4 (local)

## Servicios

- Backend (FastAPI) + Postgres: `docker-compose.dev.yml`
- Frontend (Next.js): proceso local (`npm run dev`)

## Arranque rápido

1) Levantar backend + DB:

```bash
docker compose -f docker-compose.dev.yml up -d
```

2) Migraciones + seeds:

```bash
docker exec -i decies-backend sh -lc "alembic upgrade head"
docker exec -i decies-backend sh -lc "python seed.py"
```

3) Frontend:

```bash
cd frontend
npm install
npm run dev -- -p 3000
```

## Credenciales seed

- Tutor: `tutor@decies.com` / `decies`
- Estudiante: `student@decies.com` / `decies`

## Flujo validado (E2E-04)

Objetivo: registrar calificación -> generar informe -> aceptar recomendación -> evaluar outcome -> ver impacto.

### Manual (UI)

1) En `Tutor`:
   - Añade una calificación en pestaña **Calificaciones**.
   - Genera informe y revisa **Impacto de recomendaciones**.
   - En **Recomendaciones**, acepta una recomendación y pulsa **Actualizar impacto**.

2) En `Estudiante`:
   - Completa al menos una sesión (Quiz/Examen/Match/Cloze) para generar eventos.

### Automatizado (pytest)

Ejecuta el test E2E-04:

```bash
cd backend
pytest -q tests/e2e/test_e2e_04_outcomes_report.py
```

O dentro del contenedor backend:

```bash
docker exec -i decies-backend sh -lc "pytest -q tests/e2e/test_e2e_04_outcomes_report.py"
```

