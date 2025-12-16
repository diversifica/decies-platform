# Documento 24 – Registro de Decisiones y Supuestos

## Versión 1 (Decision Log & Assumptions V1)

## 1. Propósito del documento

Este documento recoge de forma estructurada:

* Decisiones clave tomadas en el diseño y arranque del proyecto.
* Supuestos explícitos que aún no han sido validados.
* Riesgos conscientes aceptados temporalmente.
* Preguntas abiertas que deberán resolverse con datos reales.

Su objetivo es:

* Evitar pérdida de contexto en el futuro.
* Facilitar revisiones y pivotes informados.
* Separar hechos validados de hipótesis.

Este documento es **vivo** y debe actualizarse a lo largo del desarrollo.

---

## 2. Decisiones estratégicas cerradas

### D-01 – La personalización es el objetivo rector

**Decisión**
El proyecto se orienta a la individualización del aprendizaje, no a la gamificación como fin.

**Motivo**
El fracaso académico se atribuye principalmente a la enseñanza generalista, no a la falta de capacidad del alumno.

**Estado**
Cerrada – No se revisa salvo evidencia muy fuerte en contra.

---

### D-02 – El tutor siempre mantiene el control

**Decisión**
El sistema propone, el tutor decide.
No existen decisiones pedagógicas automáticas sin validación humana.

**Motivo**
Confianza, explicabilidad y cumplimiento ético/legal con menores.

**Estado**
Cerrada.

---

### D-03 – Métricas antes que modelos complejos

**Decisión**
El motor adaptativo se basa en métricas deterministas en V1, no en ML opaco.

**Motivo**
Necesidad de explicabilidad, trazabilidad y control fino del comportamiento.

**Estado**
Cerrada para V1. Reabrible en fases avanzadas.

---

### D-04 – Eventos como fuente de verdad

**Decisión**
Todo análisis se basa en eventos de aprendizaje append-only.

**Motivo**
Reprocesabilidad, auditoría y robustez del sistema.

**Estado**
Cerrada.

---

### D-05 – LLM como herramienta, no como decisor

**Decisión**
El LLM estructura, genera y redacta, pero no decide estrategias educativas.

**Motivo**
Evitar dependencia excesiva, alucinaciones y pérdida de control.

**Estado**
Cerrada.

---

## 3. Decisiones técnicas cerradas (Fase 1)

### D-06 – Stack técnico

**Decisión**

* Backend: FastAPI (Python)
* DB: PostgreSQL
* Frontend: Next.js
* Infra: Docker / docker-compose

**Motivo**
Madurez, flexibilidad, facilidad de evolución y contratación futura.

**Estado**
Cerrada para Fase 1.

---

### D-07 – Monorepo

**Decisión**
Backend, frontend y docs conviven en un único repositorio.

**Motivo**
Coherencia, trazabilidad y menor fricción en fases iniciales.

**Estado**
Cerrada.

---

### D-08 – API versionada desde el inicio

**Decisión**
Uso explícito de /api/v1.

**Motivo**
Evitar roturas futuras y permitir evolución controlada.

**Estado**
Cerrada.

---

## 4. Supuestos clave (pendientes de validar)

### S-01 – Las métricas definidas son suficientes

**Supuesto**
Las métricas V1 permiten detectar patrones útiles de aprendizaje.

**Cómo se valida**

* Observando si generan recomendaciones útiles para el tutor.
* Feedback cualitativo del tutor tras Sprint 1.

**Estado**
Pendiente de validar.

---

### S-02 – El tutor entiende y confía en los informes

**Supuesto**
El informe generado es comprensible y accionable.

**Cómo se valida**

* Tutor real o simulado leyendo informes.
* Pregunta clave: “¿Qué harías diferente después de leerlo?”

**Estado**
Pendiente de validar.

---

### S-03 – El pipeline LLM produce ítems de calidad suficiente

**Supuesto**
Los ítems generados automáticamente son válidos para practicar.

**Cómo se valida**

* Revisión manual de ítems en Sprint 1.
* Detección de ambigüedades y errores conceptuales.

**Estado**
Pendiente de validar.

---

### S-04 – La carga cognitiva del alumno es adecuada

**Supuesto**
Las sesiones y juegos no generan fatiga excesiva.

**Cómo se valida**

* Métricas de abandono y fatiga.
* Observación directa.

**Estado**
Pendiente de validar.

---

## 5. Riesgos aceptados conscientemente (Fase 1)

### R-01 – UX mínima

**Riesgo**
La experiencia visual no es atractiva.

**Motivo de aceptación**
El valor está en el motor, no en la interfaz inicial.

---

### R-02 – Pipeline LLM imperfecto

**Riesgo**
Errores de estructuración o generación.

**Motivo de aceptación**
Se prioriza trazabilidad y revisión humana.

---

### R-03 – Dataset reducido

**Riesgo**
Pocas conclusiones generalizables en fases tempranas.

**Motivo de aceptación**
La prioridad es validar el enfoque, no escalar.

---

## 6. Preguntas abiertas (a responder con datos)

* ¿Qué métricas aportan más valor real al tutor?
* ¿Qué recomendaciones se aceptan más?
* ¿Qué tipo de actividad funciona mejor por alumno?
* ¿Dónde se produce más fricción: contenido, juego o informe?
* ¿Qué partes del sistema sobran en V1?

Estas preguntas **no se responden con más diseño**, sino con uso real.

---

## 7. Política de actualización del documento

* Este documento se actualiza:

  * al final de cada sprint
  * cuando se invalida un supuesto
  * cuando se toma una decisión estructural nueva

Regla:

* Nunca borrar entradas.
* Marcar decisiones como revisadas o reemplazadas.
* Mantener histórico.

---

## 8. Nota final

Este documento existe para evitar dos errores comunes:

1. Olvidar por qué se tomaron decisiones pasadas.
2. Confundir hipótesis con verdades validadas.

Mientras este documento esté vivo y honesto,
el proyecto podrá evolucionar sin perder coherencia ni foco.
