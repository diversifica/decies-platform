# Documento 08 – Arquitectura Lógica del Sistema
## Versión 1 (Architecture V1)

## 1. Propósito del documento

Este documento define la **arquitectura lógica del sistema**, describiendo los componentes principales, sus responsabilidades y los flujos de información entre ellos.

La arquitectura está alineada con:
- Documento 01 – Objetivo Rector y Principios
- Documento 02 – Modelo de Métricas del Alumno V1
- Documento 04 – Motor de Recomendaciones V1
- Documento 07 – Modelo de Datos y Entidades V1

Este documento **no define tecnologías concretas**. Su función es servir como base estable para cualquier decisión técnica futura.

---

## 2. Principios arquitectónicos

La arquitectura del sistema se rige por los siguientes principios:

1. **Separación clara de responsabilidades**  
   Cada componente tiene una función específica y no invade responsabilidades ajenas.

2. **Flujos trazables de extremo a extremo**  
   Todo resultado (recomendación, informe) debe poder rastrearse hasta los datos de origen.

3. **Procesamiento asíncrono siempre que sea posible**  
   Las tareas intensivas (LLM, métricas, análisis) no bloquean la experiencia del usuario.

4. **Versionado explícito**  
   Reglas, métricas, contenidos y modelos se versionan para permitir evolución controlada.

5. **Control humano en decisiones clave**  
   El tutor valida y decide; el sistema propone y explica.

---

## 3. Componentes lógicos del sistema

### 3.1 Capa de Interfaz (UI Layer)

#### Componentes
- Aplicación Alumno (Jugador)
- Panel Tutor
- Panel Admin

#### Responsabilidades
- Interacción con usuarios.
- Visualización de juegos, progreso, informes y recomendaciones.
- Captura de decisiones del tutor.
- Subida y catalogación de contenido.

La capa de interfaz **no contiene lógica pedagógica ni analítica**.

---

### 3.2 Módulo de Ingesta de Contenido

#### Responsabilidades
- Recepción de PDFs e imágenes desde el tutor.
- Asociación del contenido a:
  - Alumno (opcional)
  - Asignatura
  - Trimestre
  - Tema
- Almacenamiento seguro del archivo original.
- Emisión de evento de “contenido disponible”.

Este módulo actúa como **puerta de entrada del conocimiento**.

---

### 3.3 Pipeline de Procesamiento LLM

#### Responsabilidades
- Extracción de texto (OCR / PDF).
- Estructuración del contenido académico.
- Identificación de:
  - Temas
  - Microconceptos
  - Definiciones
  - Ejemplos
- Generación de semillas para ítems evaluables.
- Registro completo de cada ejecución (trazabilidad).

El pipeline LLM:
- No interactúa directamente con el alumno.
- No toma decisiones pedagógicas finales.
- Produce **contenido estructurado versionado**.

---

### 3.4 Gestor de Conocimiento Académico

#### Responsabilidades
- Almacenar conocimiento estructurado.
- Mantener versiones de:
  - Entradas de conocimiento
  - Fragmentos (chunks)
- Relacionar conocimiento con microconceptos.
- Servir como fuente para generación de ítems.

Este módulo es el **repositorio semántico del sistema**.

---

### 3.5 Banco de Ítems y Generador de Actividades

#### Responsabilidades
- Almacenar ítems evaluables.
- Clasificar ítems por:
  - Microconcepto
  - Dificultad
  - Tipo
  - Uso (práctica, examen, transferencia)
- Seleccionar ítems para actividades según:
  - Recomendaciones activas
  - Estado del alumno
  - Configuración del tutor
- Generar sesiones de juego.

Este módulo traduce conocimiento en **experiencias evaluables**.

---

### 3.6 Motor de Juegos y Sesiones

#### Responsabilidades
- Ejecutar actividades gamificadas.
- Gestionar sesiones:
  - Inicio
  - Flujo
  - Finalización
- Controlar ayudas, ritmo y duración.
- Emitir eventos de interacción detallados.

Este módulo **no interpreta resultados**, solo los ejecuta y registra.

---

### 3.7 Sistema de Telemetría y Eventos

#### Responsabilidades
- Registrar todos los eventos de aprendizaje (append-only).
- Garantizar integridad y orden temporal.
- Servir como fuente única de verdad para analítica.

Este sistema desacopla completamente:
- Experiencia del alumno
- Análisis posterior

---

### 3.8 Motor de Métricas y Estados de Dominio

#### Responsabilidades
- Procesar eventos crudos.
- Calcular métricas agregadas por ventanas temporales.
- Actualizar estados de dominio (mastery).
- Detectar tendencias, estancamientos y alertas.

Este motor **no recomienda**, solo mide y describe.

---

### 3.9 Motor de Recomendaciones

#### Responsabilidades
- Evaluar métricas y estados frente a reglas definidas.
- Activar recomendaciones del catálogo cerrado (R01–R40).
- Priorizar recomendaciones.
- Generar evidencias explicables.
- Definir ventanas de evaluación.

Este motor:
- Es determinista.
- Es auditable.
- No ejecuta cambios automáticamente.

---

### 3.10 Gestor de Decisiones del Tutor

#### Responsabilidades
- Presentar recomendaciones al tutor.
- Registrar decisiones:
  - Aceptar
  - Rechazar
  - Posponer
- Aplicar ajustes derivados de decisiones aceptadas.
- Bloquear o revertir estrategias si el tutor lo decide.

Este módulo materializa el **control humano**.

---

### 3.11 Generador de Informes

#### Responsabilidades
- Consolidar métricas, estados y recomendaciones.
- Generar informes estructurados:
  - Resumen ejecutivo
  - Estado actual
  - Tendencias
  - Propuestas
- Versionar informes generados.
- Adaptar lenguaje al perfil del tutor.

El informe es el **principal artefacto de valor percibido**.

---

### 3.12 Integración de Evaluaciones Reales

#### Responsabilidades
- Capturar calificaciones reales.
- Asociarlas a ámbito académico.
- Detectar discrepancias con métricas internas.
- Emitir señales al motor de recomendaciones.

Este módulo conecta el sistema con el mundo educativo real.

---

## 4. Flujo lógico principal (end-to-end)

1. El tutor sube contenido académico.
2. El módulo de ingesta almacena y cataloga.
3. El pipeline LLM estructura el contenido.
4. Se generan ítems y actividades.
5. El alumno interactúa mediante juegos.
6. Se registran eventos de aprendizaje.
7. El motor de métricas calcula estados.
8. El motor de recomendaciones genera propuestas.
9. El tutor revisa y decide.
10. El sistema aplica ajustes y monitoriza impacto.
11. Se genera informe al tutor.

Este ciclo se repite de forma continua.

---

## 5. Versionado y evolución

Cada componente debe exponer:
- Versión de reglas
- Versión de métricas
- Versión de contenido
- Versión de informes

Esto permite:
- Comparar resultados entre versiones.
- Auditar decisiones pasadas.
- Evolucionar sin romper coherencia.

---

## 6. Guardarraíles del sistema

- El sistema nunca elimina contenido sin trazabilidad.
- El sistema no aplica cambios pedagógicos sin aceptación del tutor.
- El sistema no recomienda fuera del catálogo definido.
- El sistema no oculta métricas relevantes al tutor.
- El sistema prioriza estabilidad frente a optimización agresiva.

---

## 7. Alcance de la arquitectura en Fase 1

Implementación mínima viable:
- Ingesta básica
- Pipeline LLM inicial
- Banco de ítems reducido
- Motor de métricas V1
- Motor de recomendaciones V1
- Informe básico al tutor

Componentes como experimentación avanzada o modelos probabilísticos quedan fuera de esta fase.

---

## 8. Nota final

Esta arquitectura define un sistema:
- Modular
- Explicable
- Escalable
- Alineado con el objetivo rector

Cualquier implementación técnica debe respetar esta estructura lógica para preservar la coherencia del proyecto.
