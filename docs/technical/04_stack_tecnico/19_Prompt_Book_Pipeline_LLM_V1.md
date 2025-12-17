# Documento 19 – Prompt Book del Pipeline LLM

## Versión 1 (LLM Prompt Book V1)

## 1. Propósito

Este documento define el **Prompt Book** del pipeline LLM para Fase 1, incluyendo:

* Etapas del pipeline (extract → structure → map → generate items → validate)
* Prompts versionados
* Formatos de entrada/salida (JSON estricto)
* Guardarraíles de seguridad (menores, privacidad, errores)
* Criterios de calidad y validación

Objetivo principal: transformar material real (PDF/imagen) aportado por tutor en:

* conocimiento estructurado (KnowledgeEntry/KnowledgeChunk)
* microconceptos (si aplica)
* ítems evaluables (Items)
  todo con trazabilidad y versionado.

---

## 2. Principios de diseño del pipeline LLM

1. Salida estructurada en JSON estricto (sin texto extra).
2. No incluir datos personales del alumno en prompts ni outputs.
3. Reintentos controlados: máximo 2 por etapa (evitar loops).
4. Mantener trazabilidad: cada salida referencia `content_upload_id`, `llm_run_id`, `prompt_version`.
5. Calidad antes que cantidad: generar pocos ítems buenos y revisables.
6. Robustez ante ruido: tolerar OCR imperfecto sin inventar contenido.
7. Separación por etapas: cada etapa hace una sola cosa.

---

## 3. Visión del pipeline (Fase 1)

### 3.1 Etapas

E0. Preparación (sistema)

* Limpiar texto, normalizar espacios, eliminar cabeceras repetidas, detectar idioma.

E1. Extracción (si hace falta)

* Si el texto viene de OCR/PDF parser, esta etapa puede ser “passthrough” y solo normaliza.

E2. Estructuración

* Convertir texto en conocimiento estructurado: definiciones, reglas, ejemplos, resumen.

E3. Mapeo a microconceptos (opcional V1, recomendado)

* Vincular chunks a microconceptos existentes (si el tutor ya los tiene).
* Si no existen, proponer microconceptos sugeridos (sin crear automáticamente si no hay política para ello).

E4. Generación de ítems

* Crear preguntas tipo quiz: MCQ y Verdadero/Falso (mínimo).

E5. Validación

* Validación lógica: respuesta correcta, opciones plausibles, sin ambigüedad, sin contenido fuera del texto fuente.

---

## 4. Inputs estándar del pipeline

### 4.1 Input canónico para el LLM

El backend debe construir un objeto JSON (siempre igual) para todas las etapas:

```json
{
  "meta": {
    "content_upload_id": "uuid",
    "student_id": "uuid-or-null",
    "subject": {"id":"uuid","code":"MAT","name":"Matemáticas"},
    "term": {"id":"uuid","code":"T1","name":"1er Trimestre"},
    "topic": {"id":"uuid-or-null","code":"MAT_T1_01","name":"Números enteros"},
    "language": "es",
    "prompt_version": "V1",
    "engine_version": "V1"
  },
  "source": {
    "file_type": "pdf|image",
    "extraction_method": "pdf_text|vision_ocr|hybrid",
    "raw_text": "string",
    "raw_text_quality_hint": "low|medium|high"
  },
  "constraints": {
    "age_range": "12-16",
    "no_personal_data": true,
    "output_json_only": true
  }
}
```

Notas:

* `raw_text` se limita (por ejemplo) a 20k–40k caracteres por llamada, segmentando si hace falta.
* La segmentación debe preservar orden de páginas y bloques.

---

## 5. Outputs estándar y reglas de formato

### 5.1 Reglas estrictas para outputs

* Responder solo con JSON válido.
* No incluir comillas tipográficas, ni comentarios.
* No incluir Markdown.
* No incluir texto fuera del JSON.
* Campos obligatorios siempre presentes (aunque vacíos).

### 5.2 Formato de KnowledgeEntry/Chunks (salida E2)

```json
{
  "knowledge_entry": {
    "entry_version": 1,
    "status": "draft",
    "summary": "string"
  },
  "chunks": [
    {
      "chunk_type": "definition|rule|example|summary|note|exercise_seed",
      "content": "string",
      "microconcept_suggestion": {
        "code": "string-or-null",
        "name": "string-or-null"
      },
      "confidence": 0.0,
      "order_index": 0
    }
  ],
  "quality": {
    "coverage": 0.0,
    "coherence": 0.0,
    "hallucination_risk": "low|medium|high",
    "notes": ["string"]
  }
}
```

### 5.3 Formato de ítems (salida E4/E5)

```json
{
  "items": [
    {
      "item_type": "mcq|true_false",
      "stem": "string",
      "options": ["string","string","string","string"],
      "correct_answer": "string",
      "explanation": "string",
      "difficulty": 0.0,
      "microconcept_ref": {
        "microconcept_id": "uuid-or-null",
        "microconcept_code": "string-or-null",
        "microconcept_name": "string-or-null"
      },
      "source_chunk_index": 0
    }
  ],
  "quality": {
    "ambiguity_risk": "low|medium|high",
    "leakage_risk": "low|medium|high",
    "notes": ["string"]
  }
}
```

---

## 6. Guardarraíles de seguridad y privacidad

### 6.1 Prohibiciones

El LLM no debe:

* inferir datos personales (nombre real del alumno, dirección, etc.)
* generar diagnósticos clínicos o etiquetas médicas
* producir contenido inapropiado para menores
* inventar temario no presente en el texto fuente

### 6.2 Regla de oro de contenido

Si el texto fuente no contiene evidencia suficiente, el LLM debe:

* devolver `chunks` más cortos y genéricos
* marcar `hallucination_risk = "high"`
* incluir nota en `quality.notes`

---

## 7. Prompts por etapa (V1)

Todos los prompts tienen:

* System Prompt (estable)
* Task Prompt (por etapa)
* Developer Constraints (formato JSON)

### 7.1 System Prompt (común a todas las etapas)

Texto base:

Eres un motor de estructuración de contenido educativo.
Tu salida debe ser exclusivamente JSON válido.
No incluyas texto fuera del JSON.
No inventes información: utiliza solo lo que aparece en raw_text.
Si falta información, marca el riesgo de alucinación y reduce el output.
No incluyas datos personales del alumno ni inferencias sobre su identidad.
Idioma de salida: español.

---

### 7.2 E2 – Prompt de Estructuración (Structure)

#### Task Prompt (E2)

Entrada: objeto canónico (ver sección 4.1)

Instrucciones:

1. Lee raw_text y detecta los puntos clave del tema.
2. Genera:

   * summary breve (2–6 frases)
   * chunks: definiciones, reglas, ejemplos, resumen final, notas
3. Cada chunk debe ser:

   * breve y atómico (máx. 800 caracteres en Fase 1)
   * fiel al texto fuente
4. Si hay fórmulas o pasos, exprésalos en texto plano (no LaTeX).
5. Añade sugerencias de microconcepto si corresponde.

#### Output JSON Schema (E2)

Debe seguir exactamente el formato de la sección 5.2.

---

### 7.3 E3 – Prompt de Mapeo a microconceptos (Map)

#### Entrada adicional

Además del objeto canónico, el backend añade:

```json
{
  "microconcept_catalog": [
    {"id":"uuid","code":"MAT_MC_001","name":"Comparar enteros"},
    {"id":"uuid","code":"MAT_MC_002","name":"Suma y resta de enteros"}
  ],
  "chunks_from_E2": [
    {"chunk_type":"definition","content":"..."},
    {"chunk_type":"example","content":"..."}
  ]
}
```

#### Task Prompt (E3)

1. Para cada chunk, elige:

   * microconcepto existente (si encaja claramente), o
   * sugerencia (si no existe)
2. Prioriza precisión sobre cobertura.
3. No asignar microconcepto si la confianza es baja.

#### Output JSON (E3)

```json
{
  "chunk_mappings": [
    {
      "chunk_index": 0,
      "microconcept_match": {
        "microconcept_id": "uuid-or-null",
        "microconcept_code": "string-or-null",
        "microconcept_name": "string-or-null"
      },
      "confidence": 0.0,
      "reason": "string"
    }
  ],
  "quality": {
    "mapping_coverage": 0.0,
    "mapping_precision_hint": "low|medium|high",
    "notes": ["string"]
  }
}
```

---

### 7.4 E4 – Prompt de Generación de Ítems (Generate Items)

#### Entrada

* objeto canónico
* salida E2 (chunks)
* salida E3 (mapeos) si existe

#### Task Prompt (E4)

Genera ítems evaluables de tipo:

* mcq (4 opciones)
* true_false (2 opciones fijas: Verdadero/Falso)

Reglas:

1. Cada ítem debe derivarse de un chunk concreto (usar `source_chunk_index`).
2. No crear preguntas fuera del texto.
3. Evitar ambigüedad:

   * 1 sola opción claramente correcta
   * opciones distractoras plausibles pero incorrectas
4. Explicación breve (1–3 frases) apoyada en el chunk.
5. Generar pocos ítems por lote:

   * 6 a 12 ítems por content_upload (Fase 1)
6. Reparto recomendado:

   * 70% mcq
   * 30% true_false

#### Output JSON (E4)

Debe seguir exactamente el formato de la sección 5.3.

---

### 7.5 E5 – Prompt de Validación de Ítems (Validate)

#### Entrada

* lista de items del E4
* chunks del E2

#### Task Prompt (E5)

Valida cada ítem:

1. ¿La respuesta correcta se deriva del chunk indicado?
2. ¿Hay ambigüedad o doble interpretación?
3. ¿Las opciones son consistentes?
4. ¿El lenguaje es apropiado para 12–16?
5. ¿Se han colado conceptos no presentes?

Acciones:

* Si un ítem es válido: marcar `status = "ok"`.
* Si es corregible: devolver versión corregida.
* Si es inválido: devolver `status = "drop"` con razón.

#### Output JSON (E5)

```json
{
  "validated_items": [
    {
      "index": 0,
      "status": "ok|fix|drop",
      "reason": "string",
      "item": {
        "item_type": "mcq|true_false",
        "stem": "string",
        "options": ["string","string","string","string"],
        "correct_answer": "string",
        "explanation": "string",
        "difficulty": 0.0,
        "microconcept_ref": {
          "microconcept_id": "uuid-or-null",
          "microconcept_code": "string-or-null",
          "microconcept_name": "string-or-null"
        },
        "source_chunk_index": 0
      }
    }
  ],
  "quality": {
    "kept": 0,
    "fixed": 0,
    "dropped": 0,
    "notes": ["string"]
  }
}
```

---

## 8. Segmentación (cuando raw_text es grande)

### 8.1 Estrategia V1 (simple)

* Dividir por páginas o por bloques de tamaño fijo (p. ej. 15k–20k caracteres).
* Mantener orden.
* Ejecutar E2 por segmento.
* Unir resultados:

  * concatenar chunks ajustando `order_index`
  * combinar summaries (resumen de resúmenes)

### 8.2 Prompt de “Merge” (opcional)

En Fase 1 se recomienda unir en backend sin LLM.
Si se usa LLM:

* dar como input las summaries parciales y pedir un summary global.

---

## 9. Calidad: métricas y umbrales V1

### 9.1 Señales de calidad generadas por LLM

* `coverage`: 0–1 (cuánto cubre el contenido)
* `coherence`: 0–1 (coherencia interna)
* `hallucination_risk`: low/medium/high
* `ambiguity_risk`: low/medium/high

### 9.2 Regla de aceptación V1 (backend)

* Si `hallucination_risk = high` → no generar ítems, pedir revisión al tutor.
* Si `ambiguity_risk = high` → ejecutar E5 y conservar solo los “ok”.

---

## 10. Trazabilidad y registro (LLMRun)

Por cada etapa se crea un `llm_runs`:

* `run_type`: extract/structure/map/generate_items/validate
* `input_refs`: ids + hashes (sin contenido completo si es sensible)
* `output_refs`: ids creados (KnowledgeEntry, Items)
* `model_name`, `prompt_version`, `engine_version`
* `status`, `error_message`

Recomendación:

* guardar `raw_text` fuera de la tabla (en storage) y registrar `raw_text_uri`.

---

## 11. Plantillas de prompts (listas para implementar)

### 11.1 Prompt template (estructura general)

Variables:

* {{INPUT_JSON}}: el objeto de entrada serializado
* {{OUTPUT_SCHEMA_HINT}}: recordatorio del formato de salida

Plantilla:

* System: (sección 7.1)
* User: incluir:

  * "Entrada JSON:" + {{INPUT_JSON}}
  * "Devuelve solo JSON con el siguiente formato:" + {{OUTPUT_SCHEMA_HINT}}

---

## 12. Ejemplo mínimo (E2 → E4) para validar

### 12.1 Entrada (raw_text muy breve)

Ejemplo de contenido:

* definición
* regla
* ejemplo

Objetivo de prueba:

* confirmar que:

  * E2 produce chunks correctos
  * E4 produce 6 ítems consistentes
  * E5 descarta ambigüos

Nota: este ejemplo se ejecuta mejor como test automático en backend.

---

## 13. Control de costes y rendimiento (Fase 1)

* Limitar tokens por etapa.
* Limitar ítems por upload.
* Cachear resultados por `content_upload_id` y `prompt_version`.
* Evitar re-procesar si no ha cambiado el contenido.

---

## 14. Política de fallback

Si el pipeline falla:

1. Marcar `llm_runs.status = error`
2. Crear una notificación para el tutor: “contenido no estructurable automáticamente”
3. Ofrecer dos opciones:

   * reintentar con OCR alternativo
   * permitir que el tutor introduzca manualmente “microconceptos + 5 preguntas”

---

## 15. Nota final

Este Prompt Book convierte el pipeline LLM en un sistema:

* repetible
* auditable
* seguro para menores
* controlado por el tutor
* escalable por versiones

Cualquier cambio de prompts o formato debe reflejarse como:

* `prompt_version = V1.x`
* actualización de este documento
* pruebas de regresión sobre un set de contenidos de referencia
