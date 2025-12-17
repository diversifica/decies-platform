# D-09 – Orden de Scripts Init DB PostgreSQL

## Contexto

Sprint 0 - Day 1: Al configurar PostgreSQL con Docker, los scripts de inicialización en `/docker-entrypoint-initdb.d` no se ejecutaban en el orden esperado.

## Problema Detectado

**Síntoma:**
```
ERROR: relation "roles" does not exist
LINE 1: INSERT INTO roles (name, description)
```

**Causa raíz:**
PostgreSQL ejecuta scripts en orden **lexicográfico** (alfabético), no numérico.

Naming incorrecto:
- `18A_seeds.sql` (ejecutaba primero, porque 'A' < 's')
- `18_schema.sql` (ejecutaba segundo)

Resultado: `INSERT` ejecutaba antes que `CREATE TABLE` → Error.

## Decisión

**Usar prefijos numéricos secuenciales sin letras:**
- `01_schema.sql` - Schema (CREATE TABLE)
- `02_seeds.sql` - Datos iniciales (INSERT)
- `03_...` - Futuros scripts

## Alternativas Consideradas

1. ❌ **Un solo archivo init.sql**
   - Pro: Sin problemas de orden
   - Contra: Mezcla schema y seeds, menos mantenible

2. ✅ **Prefijos numéricos 01_, 02_, 03_** (ELEGIDA)
   - Pro: Orden explícito y escalable
   - Pro: Separación clara schema/seeds/migrations
   - Contra: Ninguno significativo

3. ❌ **Letras (A_, B_, C_)**
   - Pro: Orden claro
   - Contra: Límite de 26 archivos

## Implementación

```
backend/db/init/
├── 01_schema.sql     # Tablas, índices, constraints
├── 02_seeds.sql      # Datos de desarrollo/test
└── (futuros: 03_, 04_...)
```

**Importante:** Los scripts solo se ejecutan en **primer arranque** (volumen vacío).

Para forzar re-ejecución tras cambios en scripts:
```bash
docker compose -f docker-compose.dev.yml down -v  # Borra volumen
docker compose -f docker-compose.dev.yml up -d    # Re-inicializa
```

## Validación

```bash
# Verificar orden de ejecución
docker exec -it decies-db ls -la /docker-entrypoint-initdb.d

# Verificar que schema se aplicó
docker exec -it decies-db psql -U decies -d decies -c "\dt"

# Verificar que seeds se cargaron
docker exec -it decies-db psql -U decies -d decies -c "SELECT * FROM roles;"
```

## Estado

**CERRADA** - Implementado en commit `feat(sprint0): dockerized postgres with ordered init scripts`

## Referencias

- Commit: `feature/sprint0-day1-infra`
- PostgreSQL Docker docs: https://hub.docker.com/_/postgres (sección "Initialization scripts")

## Fecha

2025-12-15
