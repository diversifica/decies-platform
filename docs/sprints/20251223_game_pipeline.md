# Sprint 20251223 – Pipeline de Juegos Extensibles

## Contexto
Tras cerrar la release preprod y volver a develop, necesitamos arrancar un sprint nuevo para implementar el pipeline extensible de juegos que permita generar contenido para MATCH, CLOZE y futuros juegos desde el LLM.

## Issues

### Issue 1: Day 1 – Modelo Game y servicio admin
- **GitHub**: [#156](https://github.com/diversifica/decies-platform/issues/156)
- **PR**: [#159](https://github.com/diversifica/decies-platform/pull/159)
- **Título**: Sprint 8 Day 1: Modelo Game y servicio admin
- **Etiquetas**: `enhancement`, `backend`
- **Estimación**: 1 día
- **Estado**: ✅ Completado
- **Descripción**: Crear el modelo `Game` para configurar juegos extensibles y exponer endpoints administrativos.
- **Tareas**:
  - [x] Crear modelo `Game` con campos: code, name, item_type, prompt_template, prompt_version, engine_version, source_hint, active, last_processed_at
  - [x] Migración Alembic para tabla `games` y columna `items.source_game`
  - [x] Schemas Pydantic `GameResponse` y `GameUpdate`
  - [x] Servicio `GameService` con métodos: list_games, get_by_code, update, has_content
  - [x] Endpoints admin: GET /admin/games, PATCH /admin/games/{code}
  - [x] Seed inicial con QUIZ, MATCH, CLOZE
- **Criterios**: migración sin errores, endpoints responden, verificación de contenido, seed funcional

### Issue 2: Day 2 – Extender pipeline para multi-juego
- **GitHub**: [#157](https://github.com/diversifica/decies-platform/issues/157)
- **Título**: Sprint 8 Day 2: Extender pipeline para multi-juego
- **Etiquetas**: `enhancement`, `backend`
- **Estimación**: 1 día
- **Dependencias**: Requiere #156
- **Descripción**: Modificar `process_content_upload` para iterar sobre juegos activos y generar ítems con trazabilidad.
- **Tareas**:
  - [ ] Modificar `process_content_upload` para consultar `Game.active=True`
  - [ ] Por cada juego, construir prompt específico y llamar LLM
  - [ ] Almacenar `Item.source_game` con el código del juego
  - [ ] Registrar metadatos en `llm_runs` (game_code, prompt_version)
  - [ ] Validar que QUIZ sigue funcionando
  - [ ] Probar generación de MATCH (si hay prompt)
- **Criterios**: pipeline multi-juego funcional, trazabilidad completa, sin regresiones

### Issue 3: Day 3 – Panel admin de juegos en frontend
- **GitHub**: [#158](https://github.com/diversifica/decies-platform/issues/158)
- **Título**: Sprint 8 Day 3: Panel admin de juegos en frontend
- **Etiquetas**: `enhancement`, `frontend`
- **Estimación**: 1 día
- **Dependencias**: Requiere #156
- **Descripción**: Crear UI administrativa para gestionar juegos (activar/desactivar, ver estado).
- **Tareas**:
  - [ ] Crear pestaña "Juegos" en `/admin`
  - [ ] Listar juegos con estado (activo/inactivo, última generación)
  - [ ] Toggle para activar/desactivar juegos
  - [ ] Modal de confirmación si no hay contenido
  - [ ] Botón para disparar reprocesado (opcional)
  - [ ] Mostrar mensajes de error/éxito
- **Criterios**: el admin puede togglear cada juego, se registra la trazabilidad y se valida contenido antes de activar

## Notas de implementación
- Cada issue debe crear su propia rama desde develop siguiendo el patrón `feature/games-pipeline-dayN`
- Cada PR debe vincular la issue correspondiente con `Fixes #NNN`
- El Day 1 ya está implementado en la rama `feature/games-pipeline-day1`
- Los Days 2 y 3 se implementarán secuencialmente tras merge del anterior
