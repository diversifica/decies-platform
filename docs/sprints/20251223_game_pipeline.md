# Sprint 20251223 – Pipeline de Juegos Extensibles

## Contexto
Tras cerrar la release preprod y volver a develop, necesitamos arrancar un sprint orientado a que el pipeline LLM genere contenido para *todos* los juegos activos. El objetivo es que el backend, la UI de administración y el pipeline compartan una configuración de juegos activables, cada uno con su prompt, su tipo de item y su flag de activación.

> La propuesta se divide en issues diarios; en este documento indico qué debe contener cada uno y qué días estimados se asignan. Copia y pega en GitHub para crear los issues oficiales.

## Issues del sprint

### 1. Day 1 – Modelo y servicios base de juegos (1 día)
- Crear el modelo Game con campos como code, 
ame, description, item_type, prompt_template, prompt_version, engine_version, ctive, created_at, updated_at y un marcador source_hint para la trazabilidad.
- Añadir migración Alembic para crear la tabla y semilla inicial con los juegos existentes (QUIZ, MATCH, CLOZE, REVIEW si aplica).
- Implementar un servicio/repositorio que liste juegos, filtre por ctive y permita cambiar la bandera de activación.
- Añadir esquemas y DTOs para exponer la lista al admin (por ejemplo GameResponse, GameUpdate).
- Criterios: la API devuelve todos los juegos con sus prompts y el valor ctive, y el servicio puede activar/desactivar y devuelve un error si se intenta activar sin contenido disponible.

### 2. Day 2 – Pipeline multi-juego (2 días)
- Extender process_content_upload para iterar sobre los juegos activos y ejecutar un prompt específico por juego. El servicio LLM debe recibir el resultado del juego (game.code) para trazabilidad y Item debe incluir el campo source_game.
- Permitir configurar prompts (texto + versión) por juego, reutilizando Game.prompt_template y Game.prompt_version. Añadir tests o fixtures que validen que cada juego invoca el LLM con el prompt correcto.
- Garantizar que las salidas se validan con una versión común de E5 y que cada Item se guarda con el ItemType apropiado (MCQ, MATCH, CLOZE).
- Criterios: un upload activo genera ítems para cada juego activo, se registran en llm_runs y se pueden recuperar filtrando por source_game.

### 3. Day 3 – Panel admin y activación de juegos (1 día)
- Ampliar la pestaña “Juegos” en /admin para listar los juegos (código, nombre, descripción, prompt_version, estado, contenido disponible) y poder activarlos/desactivarlos.
- Cuando se activa un juego sin contenido, mostrar aviso y ofrecer lanzar un reprocesado del upload (trigger que llame al backend para procesar el contenido que falta).
- Añadir endpoints GET /api/v1/admin/games, PATCH /api/v1/admin/games/{code}, POST /api/v1/admin/games/{code}/process que controlen la activación y disparen re-procesos.
- Criterios: el admin puede togglear cada juego, se registra la trazabilidad y se confirma si hay contenido asociado; si no, el backend responde 409 con mensaje “procesar contenido primero”.

## Siguientes pasos después del sprint
1. Registrar cada issue en GitHub bajo la milestone / sprint correspondiente.
2. Implementar el Day 1 en la rama eature/games-pipeline-day1 (ya iniciada).
3. Avanzar con Day 2/3 siguiendo esta guía una vez el Day 1 esté terminado y revisado.

---
*Cuando se creen los issues reales en GitHub, referencia este documento y enlaza cada uno con Fixes #ISSUE_NUMBER.*
