# Runbook — Async Queue (Redis + RQ)

Este runbook habilita la cola asíncrona opcional para:
- Procesamiento de uploads (pipeline LLM).
- Recalcular métricas + generar recomendaciones al cerrar sesión.

## Servicios (docker compose)

Arranca DB + Redis + Backend + Worker:

```bash
docker compose -f docker-compose.dev.yml up -d --build
```

Logs del worker:

```bash
docker logs -f decies-worker
```

## Activar modo async

En `.env` (o en variables de entorno) añade:

```bash
ASYNC_QUEUE_ENABLED=true
```

Por defecto, `REDIS_URL` apunta a `redis://redis:6379/0` en docker compose.

## Ver estado de jobs (básico)

Ver cola / workers:

```bash
docker exec -i decies-worker rq info -u redis://redis:6379/0
```

Listar jobs en cola:

```bash
docker exec -i decies-worker rq list -u redis://redis:6379/0
```

## Volver a modo “no cola”

Quita `ASYNC_QUEUE_ENABLED=true` (o ponlo en `false`) y reinicia:

```bash
docker compose -f docker-compose.dev.yml restart backend
```

## Healthchecks (API)

- Redis: `GET http://localhost:8000/health/redis`
- Worker (solo si `ASYNC_QUEUE_ENABLED=true`): `GET http://localhost:8000/health/worker`

Nota: con `ASYNC_QUEUE_ENABLED=false`, `/health/worker` responde `status=skipped`.
