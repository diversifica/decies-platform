# Documento 09 – Flujos y Casos de Uso del Sistema
## Versión 1 (Use Cases & Flows V1)

## 1. Propósito del documento

Este documento describe los **flujos funcionales y casos de uso principales** del sistema, desde la perspectiva de los distintos roles (Alumno, Tutor y Admin).

Su objetivo es:
- Traducir la arquitectura lógica en interacciones reales.
- Definir comportamientos esperados del sistema.
- Servir de base para diseño UX, backlog técnico y validación funcional.

Este documento no define interfaz gráfica ni detalles técnicos de implementación.

---

## 2. Actores del sistema

### 2.1 Alumno (Jugador)
- Interactúa con actividades gamificadas.
- No gestiona contenido ni reglas.
- Genera datos mediante su interacción.

### 2.2 Tutor (Padre/Madre/Tutor legal)
- Gestiona contenido académico.
- Supervisa progreso.
- Toma decisiones pedagógicas basadas en informes y recomendaciones.

### 2.3 Administrador
- Configura el sistema.
- Mantiene catálogos y reglas.
- Supervisa el funcionamiento global.

---

## 3. Flujo F1 – Alta y configuración inicial del alumno

### Actor principal
Tutor

### Descripción
El tutor crea el perfil del alumno y define el contexto académico inicial.

### Pasos
1. El tutor crea un nuevo alumno.
2. Selecciona nivel educativo (ej. ESO).
3. Asocia asignaturas activas.
4. Selecciona trimestre activo.
5. Define límites iniciales (tiempo semanal, duración de sesiones).

### Resultado
Alumno preparado para comenzar con enseñanza genérica.

---

## 4. Flujo F2 – Subida y catalogación de contenido académico

### Actor principal
Tutor

### Descripción
El tutor aporta material real de estudio que servirá como base del aprendizaje.

### Pasos
1. El tutor sube un PDF o imagen.
2. Clasifica el contenido:
   - Asignatura
   - Trimestre
   - Tema (opcional)
3. Confirma el envío.

### Resultado
Contenido almacenado y enviado al pipeline de procesamiento LLM.

---

## 5. Flujo F3 – Procesamiento y estructuración del contenido

### Actor principal
Sistema (Pipeline LLM)

### Descripción
El sistema transforma contenido bruto en conocimiento estructurado.

### Pasos
1. Extracción de texto (OCR/PDF).
2. Identificación de conceptos y microconceptos.
3. Generación de fragmentos estructurados.
4. Creación de semillas para ítems evaluables.
5. Registro completo de la ejecución.

### Resultado
Conocimiento estructurado disponible para generar actividades.

---

## 6. Flujo F4 – Generación de actividades de aprendizaje

### Actor principal
Sistema

### Descripción
El sistema crea actividades adaptadas al estado actual del alumno.

### Pasos
1. Consulta el estado de dominio del alumno.
2. Consulta recomendaciones activas.
3. Selecciona ítems adecuados.
4. Genera una sesión de actividad.

### Resultado
Actividad lista para ser ejecutada por el alumno.

---

## 7. Flujo F5 – Sesión de juego/aprendizaje del alumno

### Actor principal
Alumno

### Descripción
El alumno interactúa con la actividad gamificada.

### Pasos
1. El alumno inicia la sesión.
2. Responde a ítems.
3. Solicita ayudas si están disponibles.
4. Finaliza o abandona la sesión.

### Resultado
Eventos de aprendizaje registrados en el sistema.

---

## 8. Flujo F6 – Registro de eventos y métricas

### Actor principal
Sistema

### Descripción
El sistema analiza la interacción del alumno.

### Pasos
1. Registro de eventos crudos.
2. Agregación por ventanas temporales.
3. Actualización del estado de dominio.
4. Detección de tendencias.

### Resultado
Métricas y estados actualizados.

---

## 9. Flujo F7 – Generación de recomendaciones pedagógicas

### Actor principal
Sistema (Motor de Recomendaciones)

### Descripción
El sistema evalúa métricas y propone ajustes.

### Pasos
1. Evaluación de métricas frente a reglas.
2. Activación de recomendaciones del catálogo.
3. Priorización.
4. Generación de evidencias.

### Resultado
Recomendaciones disponibles para el tutor.

---

## 10. Flujo F8 – Revisión y decisión del tutor

### Actor principal
Tutor

### Descripción
El tutor analiza recomendaciones y decide.

### Pasos
1. El tutor consulta las recomendaciones.
2. Revisa evidencias y justificación.
3. Acepta, rechaza o pospone cada recomendación.

### Resultado
Decisiones registradas y ajustes aplicados.

---

## 11. Flujo F9 – Generación del informe automático

### Actor principal
Sistema

### Descripción
El sistema genera un informe estructurado.

### Pasos
1. Consolida métricas, estados y recomendaciones.
2. Integra calificaciones reales si existen.
3. Redacta informe en lenguaje pedagógico.
4. Versiona y almacena el informe.

### Resultado
Informe disponible para el tutor.

---

## 12. Flujo F10 – Introducción de calificaciones reales

### Actor principal
Tutor

### Descripción
El tutor introduce resultados académicos reales.

### Pasos
1. Introduce calificación.
2. Etiqueta contenido evaluado (si es posible).
3. Confirma registro.

### Resultado
Datos externos integrados en el sistema.

---

## 13. Flujo F11 – Evaluación del impacto de recomendaciones

### Actor principal
Sistema

### Descripción
El sistema evalúa si las recomendaciones funcionan.

### Pasos
1. Finaliza la ventana de evaluación.
2. Compara métricas antes y después.
3. Marca resultado (éxito, parcial, sin efecto).
4. Emite nuevas señales si procede.

### Resultado
Aprendizaje del sistema y posibles nuevas propuestas.

---

## 14. Casos de uso resumidos

### UC-01
Crear alumno y configurar curso.

### UC-02
Subir y estructurar contenido académico.

### UC-03
Generar actividades adaptadas.

### UC-04
Jugar y registrar aprendizaje.

### UC-05
Analizar métricas y estados.

### UC-06
Proponer recomendaciones.

### UC-07
Decidir ajustes pedagógicos.

### UC-08
Generar y consultar informes.

### UC-09
Introducir notas reales.

### UC-10
Evaluar impacto y reajustar.

---

## 15. Escenarios de error y control

- Contenido no procesable → notificación al tutor.
- Datos insuficientes → el sistema no recomienda.
- Señales contradictorias → recomendación de revisión tutor–alumno.
- Tutor inactivo → sistema mantiene estrategia actual.

---

## 16. Nota final

Estos flujos describen el comportamiento esperado del sistema en condiciones normales y sirven como referencia para:
- Diseño UX/UI
- Desarrollo backend y frontend
- Testing funcional
- Validación con usuarios reales

Cualquier nuevo flujo debe añadirse como nueva versión del documento.
