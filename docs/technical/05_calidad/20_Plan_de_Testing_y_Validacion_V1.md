# Documento 20 – Plan de Testing y Validación

## Versión 1 (Testing & Validation Plan V1)

## 1. Propósito

Este documento define un plan de testing y validación para Fase 1, cubriendo:

* Pruebas de base de datos (DDL + seeds)
* Pruebas de API (contrato y autorización por roles)
* Pruebas de pipeline LLM (estructura, ítems, validación y guardarraíles)
* Pruebas de extremo a extremo (E2E) con datos reales/simulados
* Criterios de aceptación y regresión

Objetivo: garantizar que el sistema es:

* trazable
* determinista donde debe serlo
* seguro con datos de menores
* y funcional de extremo a extremo

---

## 2. Estrategia de testing (pirámide)

1. Unit tests (rápidos)

* Reglas de recomendaciones
* Cálculo de métricas
* Normalización de eventos

2. Integration tests (media)

* API + DB
* Seeds + consultas reales
* Pipeline LLM con outputs simulados (mocks)

3. Contract tests (alta prioridad)

* OpenAPI / contrato de endpoints
* Validación de schemas JSON del LLM

4. E2E tests (pocos pero críticos)

* Tutor sube contenido → alumno juega → tutor recibe recomendación

---

## 3. Entornos de prueba

### 3.1 Entorno local (dev)

* PostgreSQL en docker-compose
* FastAPI en modo dev
* Frontend opcional (mockable)

### 3.2 Entorno CI

* Base de datos efímera
* Seeds aplicados en pipeline
* Ejecución automática de tests

### 3.3 Entorno staging (recomendado)

* Similar a producción
* Datos sintéticos
* Pruebas E2E con usuarios controlados

---

## 4. Testing de Base de Datos (DDL + Seeds)

### 4.1 Objetivos

* El DDL se aplica sin errores.
* Las restricciones e índices funcionan.
* Los seeds cargan y son coherentes.

### 4.2 Casos de prueba mínimos

#### DB-01 Aplicación DDL

* Acción: ejecutar Documento 18 (DDL).
* Esperado: sin errores; tablas y tipos creados.

#### DB-02 Aplicación Seeds

* Acción: ejecutar Documento 18A.
* Esperado:

  * 1 academic_year activo
  * 3 terms creados
  * subjects MAT/LEN/HIS presentes
  * recommendation_catalog con 40 filas

#### DB-03 Integridad referencial básica

* Acción: intentar insertar microconcept con subject_id inexistente.
* Esperado: error por FK.

#### DB-04 Unicidad crítica

* Acción: insertar 2 usuarios con mismo email.
* Esperado: error por UNIQUE.

#### DB-05 Append-only eventos (política)

* Acción: actualizar un learning_event (si se permite a nivel DB).
* Esperado: en V1 se controla en backend; test asegura que el backend no expone UPDATE/DELETE.

---

## 5. Testing de API (Contrato, Roles, Funcionalidad)

### 5.1 Objetivos

* Cumplir contrato Doc 17.
* Autorizar por roles correctamente.
* Respuestas y errores consistentes.

### 5.2 Pruebas de contrato (OpenAPI)

#### API-C-01 OpenAPI válido

* Acción: generar OpenAPI desde FastAPI.
* Esperado: schema válido y versionado /api/v1.

#### API-C-02 Schemas de request/response

* Acción: validar que cada endpoint devuelve exactamente los campos definidos.
* Esperado: no faltan campos obligatorios.

### 5.3 Pruebas de autorización (RBAC)

#### API-A-01 Tutor crea alumno

* Actor: TUTOR
* Endpoint: POST /students
* Esperado: 201

#### API-A-02 Alumno intenta crear alumno

* Actor: PLAYER
* Endpoint: POST /students
* Esperado: 403

#### API-A-03 Tutor solo ve sus alumnos

* Actor: TUTOR_A y TUTOR_B
* Endpoint: GET /students
* Esperado: cada uno ve únicamente los suyos.

### 5.4 Pruebas funcionales mínimas

#### API-F-01 Subida contenido

* Actor: TUTOR
* Endpoint: POST /content/uploads
* Esperado: 201 + id

#### API-F-02 Crear sesión actividad

* Actor: TUTOR o sistema (según diseño)
* Endpoint: POST /activities/sessions
* Esperado: 201 + items

#### API-F-03 Responder ítem

* Actor: PLAYER
* Endpoint: POST /activities/sessions/{id}/responses
* Esperado: 200 + is_correct + se inserta learning_event

#### API-F-04 Finalizar sesión

* Actor: PLAYER
* Endpoint: POST /activities/sessions/{id}/end
* Esperado: 200 + status completed/abandoned

#### API-F-05 Recomendaciones visibles

* Actor: TUTOR
* Endpoint: GET /students/{id}/recommendations
* Esperado: 200 + lista coherente

#### API-F-06 Decisión tutor

* Actor: TUTOR
* Endpoint: POST /recommendations/{id}/decision
* Esperado: 200 + estado actualizado + auditoría

---

## 6. Testing del Pipeline LLM (Doc 19)

### 6.1 Objetivos

* Outputs JSON estrictos.
* Sin alucinaciones ni temario inventado.
* Ítems consistentes, no ambiguos.
* Guardarraíles de menores y privacidad.

### 6.2 Tipos de pruebas

A) Pruebas con mocks (unit/integration)

* Simular salidas LLM para testear persistencia y flujos.

B) Pruebas reales (staging)

* Ejecutar con un modelo real y datasets controlados.

### 6.3 Contratos de salida (JSON Schema)

Definir JSON Schemas para:

* E2 output (knowledge_entry + chunks + quality)
* E3 output (chunk_mappings + quality)
* E4 output (items + quality)
* E5 output (validated_items + quality)

Caso base: si el output no valida el schema → el pipeline falla y se registra error.

### 6.4 Casos de prueba críticos (LLM)

#### LLM-01 Texto limpio y completo (happy path)

Entrada: raw_text de calidad alta.
Esperado:

* E2 chunks coherentes, coverage >= 0.6, hallucination_risk low/medium
* E4 6–12 ítems, ambiguity_risk low/medium
* E5 kept >= 70%

#### LLM-02 OCR malo / texto con ruido

Entrada: raw_text_quality_hint low.
Esperado:

* E2 reduce chunks, hallucination_risk medium/high
* Si high: no generar ítems y notificar revisión tutor

#### LLM-03 Texto muy corto

Entrada: raw_text insuficiente.
Esperado:

* E2 coverage bajo, hallucination_risk high
* Ítems no se generan

#### LLM-04 Contenido ambiguo

Entrada: definiciones confusas.
Esperado:

* E4 ambiguity_risk high
* E5 drop de ítems ambiguos

#### LLM-05 Intento de contenido fuera del currículo

Entrada: texto que incluye información no académica.
Esperado:

* E2 filtra y produce solo chunks educativos.
* No introducir contenido extra.

#### LLM-06 Datos personales en el contenido

Entrada: PDF con nombre/datos del alumno (posible).
Esperado:

* E2 no copia datos personales en chunks ni ítems.
* quality.notes incluye advertencia de sanitización.

---

## 7. Testing del Motor de Métricas (V1)

### 7.1 Objetivos

* Cálculos correctos de métricas base.
* Recalculable desde eventos.
* Consistencia temporal.

### 7.2 Casos de prueba

#### MTR-01 Accuracy

Dado: 10 eventos ANSWER, 7 correctos.
Esperado: accuracy = 0.7

#### MTR-02 First attempt accuracy

Dado: mismos ítems con múltiples intentos.
Esperado: first_attempt_accuracy solo cuenta intento 1.

#### MTR-03 Tiempo mediano

Dado: tiempos [500, 1000, 1500].
Esperado: median_response_time_ms = 1000

#### MTR-04 Fatiga intrasesión

Dado: accuracy cae con el orden del ítem.
Esperado: fatigue_slope negativo.

#### MTR-05 Recalcular

Dado: recalcular ventana completa.
Esperado: resultados idénticos y versionados.

---

## 8. Testing del Motor de Recomendaciones (V1)

### 8.1 Objetivos

* Determinismo.
* Evidencias coherentes.
* No recomendar fuera del catálogo.

### 8.2 Casos de prueba

#### REC-01 R01 por mastery bajo

Entrada: mastery_score < umbral en microconceptos.
Esperado: se crea recommendation_instance R01 con priority high.

#### REC-02 R21 por fatiga

Entrada: fatigue_slope negativo + abandono alto.
Esperado: R21 se activa.

#### REC-03 No hay datos suficientes

Entrada: pocos eventos.
Esperado: no recomienda o recomienda "mantener" según política.

#### REC-04 Evidencias obligatorias

Entrada: recomendación creada.
Esperado: recommendation_evidence no vacío (mínimo 1 métrica).

#### REC-05 Determinismo

Entrada: mismo set de métricas 2 veces.
Esperado: mismo resultado.

---

## 9. E2E Testing (flujo crítico)

### 9.1 Flujo E2E-01 (mínimo viable)

1. Tutor crea alumno y contexto (T1 + MAT).
2. Tutor sube PDF simple.
3. Pipeline LLM genera items.
4. Alumno completa un quiz.
5. Se registran eventos.
6. Motor de métricas calcula mastery.
7. Motor de recomendaciones crea al menos 1 recomendación.
8. Tutor la visualiza y acepta/rechaza.
9. Se genera un reporte on-demand.

Criterio de éxito:

* todo trazable, sin intervención manual en base de datos.

---

## 10. Datasets de referencia (regresión)

Definir un set mínimo de contenidos para evitar regresiones:

* DS-01: Matemáticas enteros (texto limpio)
* DS-02: Lengua ortografía (texto medio)
* DS-03: PDF escaneado (OCR malo)
* DS-04: Texto corto (insuficiente)
* DS-05: Contenido ambiguo

Regla:

* Cada cambio en prompts o métricas debe ejecutarse contra DS-01..DS-05.
* Se comparan resultados con una baseline aprobada.

---

## 11. Criterios de aceptación global (Fase 1)

El sistema se considera “validado” para Fase 1 si:

1. Contrato API estable y probado.
2. Pipeline LLM produce conocimiento e ítems sin alucinaciones relevantes.
3. Eventos registran interacción real.
4. Métricas se calculan de forma consistente.
5. Recomendaciones son explicables y deterministas.
6. Tutor puede decidir y ver impacto en reportes.
7. No hay exposición de datos personales del menor en outputs LLM ni en logs.

---

## 12. Automatización recomendada en CI

En cada commit:

* Lint + type checks (backend)
* Unit tests (métricas, recomendaciones)
* Integration tests (API + DB)
* Validación OpenAPI
* Validación JSON Schemas (LLM outputs simulados)
* Migraciones Alembic aplican + rollback (si aplica)

En nightly:

* E2E completo (con dataset de referencia)
* Pruebas LLM reales (si hay entorno y presupuesto)

---

## 13. Nota final

Este plan busca minimizar incertidumbre y evitar que el sistema evolucione sin control.

La regla base:
Si no se puede testear, no se considera estable.
Si no se puede explicar, no se considera válido.
