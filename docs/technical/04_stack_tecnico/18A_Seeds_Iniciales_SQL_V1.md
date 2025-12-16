# Documento 18A – Seeds Iniciales (SQL)

## Versión 1 (PostgreSQL Seed Data V1)

Este archivo contiene seeds iniciales para:

* Año académico y trimestres
* Asignaturas (ejemplo)
* Topics y microconceptos (ejemplo mínimo)
* Catálogo de recomendaciones R01–R40

Copia y ejecuta este SQL en tu base de datos después de aplicar el DDL del Documento 18.

```sql
-- ============================================================
-- Seeds iniciales (Documento 18A) - PostgreSQL
-- ============================================================

-- 1) Año académico y trimestres
INSERT INTO academic_years (name, start_date, end_date, status)
VALUES ('2025-2026', '2025-09-01', '2026-06-30', 'active')
ON CONFLICT (name) DO NOTHING;

-- Recuperar id del año (para usar en inserts de terms)
WITH ay AS (
  SELECT id FROM academic_years WHERE name = '2025-2026' LIMIT 1
)
INSERT INTO terms (academic_year_id, code, name, start_date, end_date, status)
SELECT ay.id, t.code, t.name, t.start_date, t.end_date, 'active'
FROM ay
JOIN (VALUES
  ('T1','1er Trimestre','2025-09-01'::date,'2025-12-20'::date),
  ('T2','2º Trimestre','2026-01-08'::date,'2026-03-25'::date),
  ('T3','3er Trimestre','2026-04-07'::date,'2026-06-30'::date)
) AS t(code,name,start_date,end_date) ON TRUE
ON CONFLICT (academic_year_id, code) DO NOTHING;

-- 2) Asignaturas (ejemplo base ESO)
INSERT INTO subjects (code, name, level, active)
VALUES
  ('MAT','Matemáticas','ESO',true),
  ('LEN','Lengua','ESO',true),
  ('HIS','Historia','ESO',true)
ON CONFLICT (code) DO NOTHING;

-- 3) Topics y microconceptos de ejemplo (mínimo para pruebas Sprint 0/1)
-- Nota: esto es solo un ejemplo para tener datos con los que probar el pipeline.
-- Puedes borrar o ampliar posteriormente.

-- Obtener ids base
WITH
  s_mat AS (SELECT id AS subject_id FROM subjects WHERE code='MAT' LIMIT 1),
  s_len AS (SELECT id AS subject_id FROM subjects WHERE code='LEN' LIMIT 1),
  t1 AS (SELECT id AS term_id FROM terms WHERE code='T1' LIMIT 1)

-- Topics Matemáticas (T1)
INSERT INTO topics (subject_id, term_id, code, name, order_index)
SELECT s_mat.subject_id, t1.term_id, x.code, x.name, x.order_index
FROM s_mat, t1
JOIN (VALUES
  ('MAT_T1_01','Números enteros',1),
  ('MAT_T1_02','Fracciones',2)
) AS x(code,name,order_index) ON TRUE
ON CONFLICT DO NOTHING;

-- Topics Lengua (T1)
WITH
  s_len AS (SELECT id AS subject_id FROM subjects WHERE code='LEN' LIMIT 1),
  t1 AS (SELECT id AS term_id FROM terms WHERE code='T1' LIMIT 1)
INSERT INTO topics (subject_id, term_id, code, name, order_index)
SELECT s_len.subject_id, t1.term_id, x.code, x.name, x.order_index
FROM s_len, t1
JOIN (VALUES
  ('LEN_T1_01','Ortografía básica',1),
  ('LEN_T1_02','Comprensión lectora',2)
) AS x(code,name,order_index) ON TRUE
ON CONFLICT DO NOTHING;

-- Microconceptos Matemáticas (T1) asociados a topics
WITH
  s_mat AS (SELECT id AS subject_id FROM subjects WHERE code='MAT' LIMIT 1),
  t1 AS (SELECT id AS term_id FROM terms WHERE code='T1' LIMIT 1),
  tp1 AS (SELECT id AS topic_id FROM topics WHERE code='MAT_T1_01' LIMIT 1),
  tp2 AS (SELECT id AS topic_id FROM topics WHERE code='MAT_T1_02' LIMIT 1)
INSERT INTO microconcepts (subject_id, term_id, topic_id, code, name, description, active)
SELECT s_mat.subject_id, t1.term_id, tp.topic_id, m.code, m.name, m.description, true
FROM s_mat, t1
JOIN (VALUES
  ('MAT_MC_001','Comparar enteros','Comparación y orden de números enteros','MAT_T1_01'),
  ('MAT_MC_002','Suma y resta de enteros','Operaciones básicas con enteros','MAT_T1_01'),
  ('MAT_MC_003','Concepto de fracción','Parte-todo y representación','MAT_T1_02'),
  ('MAT_MC_004','Fracciones equivalentes','Simplificación y equivalencias','MAT_T1_02')
) AS m(code,name,description,topic_code) ON TRUE
JOIN LATERAL (
  SELECT id AS topic_id FROM topics WHERE code = m.topic_code LIMIT 1
) AS tp ON TRUE
ON CONFLICT DO NOTHING;

-- Microconceptos Lengua (T1)
WITH
  s_len AS (SELECT id AS subject_id FROM subjects WHERE code='LEN' LIMIT 1),
  t1 AS (SELECT id AS term_id FROM terms WHERE code='T1' LIMIT 1)
INSERT INTO microconcepts (subject_id, term_id, topic_id, code, name, description, active)
SELECT s_len.subject_id, t1.term_id, tp.topic_id, m.code, m.name, m.description, true
FROM s_len, t1
JOIN (VALUES
  ('LEN_MC_001','Uso de b/v','Reglas ortográficas básicas b/v','LEN_T1_01'),
  ('LEN_MC_002','Uso de g/j','Reglas ortográficas básicas g/j','LEN_T1_01'),
  ('LEN_MC_003','Idea principal','Identificación de la idea principal en un texto','LEN_T1_02'),
  ('LEN_MC_004','Inferencias','Deducción de información implícita','LEN_T1_02')
) AS m(code,name,description,topic_code) ON TRUE
JOIN LATERAL (
  SELECT id AS topic_id FROM topics WHERE code = m.topic_code LIMIT 1
) AS tp ON TRUE
ON CONFLICT DO NOTHING;

-- 4) Catálogo de recomendaciones (R01–R40) - V1
-- Importante: el catálogo es estable y versionable. No lo borres, actualiza por versión.
INSERT INTO recommendation_catalog (code, title, description, category, active, catalog_version)
VALUES
('R01','Priorizar microconceptos en riesgo','Enfocar práctica en microconceptos con dominio bajo y errores recurrentes.','focus',true,'V1'),
('R02','Consolidar microconceptos en progreso','Aumentar práctica para microconceptos con dominio medio e inconsistencia.','focus',true,'V1'),
('R03','Repaso espaciado de microconceptos dominados','Programar repasos para mantener retención en conceptos ya dominados.','focus',true,'V1'),
('R04','Reducir carga de nuevos conceptos','Disminuir introducción de nuevo contenido si hay demasiados conceptos en riesgo.','focus',true,'V1'),
('R05','Reforzar prerequisitos','Volver a prerequisitos cuando se detecten fallos base repetidos.','focus',true,'V1'),
('R06','Reorganizar orden del trimestre','Reordenar el plan cuando la secuencia actual no es óptima para el alumno.','focus',true,'V1'),
('R07','Aumentar repetición inmediata tras errores','Aplicar repetición inmediata para corregir errores persistentes.','focus',true,'V1'),
('R08','Introducir microevaluaciones frecuentes','Usar comprobaciones cortas y frecuentes para detectar fallos pronto.','focus',true,'V1'),
('R09','Separar conceptos confundidos','Desambiguar conceptos similares mediante práctica diferenciada.','focus',true,'V1'),
('R10','Simplificar dificultad temporalmente','Bajar dificultad para recuperar confianza y evitar bloqueo.','focus',true,'V1'),

('R11','Aumentar recuperación sin ayudas','Reducir dependencia de ayudas incrementando práctica de recuperación.','strategy',true,'V1'),
('R12','Limitar uso de pistas','Limitar pistas si se detecta dependencia excesiva.','strategy',true,'V1'),
('R13','Sustituir repaso pasivo por práctica activa','Reemplazar lectura/teoría por ejercicios de recuperación.','strategy',true,'V1'),
('R14','Introducir intercalado','Mezclar temas para mejorar discriminación y transferencia.','strategy',true,'V1'),
('R15','Volver a práctica bloqueada','Volver a práctica por bloques si el intercalado empeora el rendimiento.','strategy',true,'V1'),
('R16','Cambiar tipo de actividad','Cambiar formato de juego hacia el más eficaz para el alumno.','strategy',true,'V1'),
('R17','Aumentar ejemplos concretos','Añadir ejemplos guiados si hay errores conceptuales persistentes.','strategy',true,'V1'),
('R18','Introducir variabilidad controlada','Añadir variabilidad cuando hay dominio aparente pero baja transferencia.','strategy',true,'V1'),
('R19','Añadir explicación tras error','Mostrar explicación breve tras error cuando el mismo error se repite.','strategy',true,'V1'),
('R20','Reducir explicación anticipada','Evitar explicación previa excesiva cuando el alumno aprende bien por ensayo.','strategy',true,'V1'),

('R21','Reducir duración de sesiones','Acortar sesiones si hay fatiga intrasesión detectada.','dosage',true,'V1'),
('R22','Aumentar sesiones cortas','Aumentar frecuencia de sesiones breves si mejoran el rendimiento.','dosage',true,'V1'),
('R23','Introducir descansos','Insertar descansos si aumenta el abandono o baja la atención.','dosage',true,'V1'),
('R24','Ajustar ritmo','Ajustar ritmo de presentación según balance tiempo/accuracy.','dosage',true,'V1'),
('R25','Añadir pausa reflexiva','Añadir pausas si responde demasiado rápido con muchos errores.','dosage',true,'V1'),
('R26','Aumentar automatización','Aumentar práctica para reducir tiempo de respuesta manteniendo accuracy.','dosage',true,'V1'),
('R27','Reducir volumen diario','Reducir carga diaria si hay retroceso por exceso de volumen.','dosage',true,'V1'),
('R28','Incrementar volumen','Aumentar carga si hay dominio estable y margen de progreso.','dosage',true,'V1'),
('R29','Ajustar dificultad','Subir dificultad cuando el alumno se mantiene estable en alto rendimiento.','dosage',true,'V1'),
('R30','Alternar días intensivos y ligeros','Alternar intensidad para estabilizar rendimiento semanal.','dosage',true,'V1'),

('R31','Ejercicios tipo examen','Introducir ejercicios tipo examen si hay discrepancia con nota real.','external_validation',true,'V1'),
('R32','Revisar alineación temario','Revisar si los ítems cubren el temario real evaluado.','external_validation',true,'V1'),
('R33','Etiquetado por tutor','Solicitar más contexto/etiquetado cuando la evaluación real es ambigua.','external_validation',true,'V1'),
('R34','Reforzar transferencia','Reforzar transferencia cuando falla en ítems nuevos pese a buen desempeño.','external_validation',true,'V1'),
('R35','Priorizar conceptos clave del examen','Priorizar conceptos marcados como clave por su peso evaluativo.','external_validation',true,'V1'),
('R36','Reducir confianza excesiva','Detectar falso dominio y ajustar cuando el examen contradice el desempeño.','external_validation',true,'V1'),
('R37','Revisar consistencia entre sesiones','Revisar variabilidad alta entre sesiones para evitar diagnósticos erróneos.','external_validation',true,'V1'),
('R38','Activar revisión tutor–alumno','Proponer revisión conjunta cuando hay señales contradictorias.','external_validation',true,'V1'),
('R39','Mantener estrategia actual','Mantener estrategia si hay mejora sostenida y consistente.','external_validation',true,'V1'),
('R40','Reevaluar tras no mejora','Reevaluar estrategia si no hay mejora tras ventana de evaluación.','external_validation',true,'V1')
ON CONFLICT (code) DO NOTHING;

-- ============================================================
-- Fin seeds
-- ============================================================
```
