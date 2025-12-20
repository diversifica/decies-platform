"""add recommendation catalog

Revision ID: b3cfe90abd0c
Revises: 2f1c7f3b0b0a
Create Date: 2025-12-20 23:27:36.291628

"""

from __future__ import annotations

import uuid

import sqlalchemy as sa

from alembic import op

revision: str = "b3cfe90abd0c"
down_revision: str | None = "2f1c7f3b0b0a"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    recommendation_catalog = op.create_table(
        "recommendation_catalog",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("catalog_version", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    rows: list[dict[str, object]] = []
    base = {
        "active": True,
        "catalog_version": "V1",
    }

    def add(code: str, title: str, description: str, category: str) -> None:
        rows.append(
            {
                **base,
                "id": uuid.uuid4(),
                "code": code,
                "title": title,
                "description": description,
                "category": category,
            }
        )

    # Focus (R01-R10)
    add(
        "R01",
        "Priorizar microconceptos en riesgo",
        "Enfocar práctica en microconceptos con dominio bajo y errores recurrentes.",
        "focus",
    )
    add(
        "R02",
        "Consolidar microconceptos en progreso",
        "Aumentar práctica para microconceptos con dominio medio e inconsistencia.",
        "focus",
    )
    add(
        "R03",
        "Repaso espaciado de microconceptos dominados",
        "Programar repasos para mantener retención en conceptos ya dominados.",
        "focus",
    )
    add(
        "R04",
        "Reducir carga de nuevos conceptos",
        "Disminuir introducción de nuevo contenido si hay demasiados conceptos en riesgo.",
        "focus",
    )
    add(
        "R05",
        "Reforzar prerequisitos",
        "Volver a prerequisitos cuando se detecten fallos base repetidos.",
        "focus",
    )
    add(
        "R06",
        "Reorganizar orden del trimestre",
        "Reordenar el plan cuando la secuencia actual no es óptima para el alumno.",
        "focus",
    )
    add(
        "R07",
        "Aumentar repetición inmediata tras errores",
        "Aplicar repetición inmediata para corregir errores persistentes.",
        "focus",
    )
    add(
        "R08",
        "Introducir microevaluaciones frecuentes",
        "Usar comprobaciones cortas y frecuentes para detectar fallos pronto.",
        "focus",
    )
    add(
        "R09",
        "Separar conceptos confundidos",
        "Desambiguar conceptos similares mediante práctica diferenciada.",
        "focus",
    )
    add(
        "R10",
        "Simplificar dificultad temporalmente",
        "Bajar dificultad para recuperar confianza y evitar bloqueo.",
        "focus",
    )

    # Strategy (R11-R20)
    add(
        "R11",
        "Aumentar recuperación sin ayudas",
        "Reducir dependencia de ayudas incrementando práctica de recuperación.",
        "strategy",
    )
    add(
        "R12",
        "Limitar uso de pistas",
        "Limitar pistas si se detecta dependencia excesiva.",
        "strategy",
    )
    add(
        "R13",
        "Sustituir repaso pasivo por práctica activa",
        "Reemplazar lectura/teoría por ejercicios de recuperación.",
        "strategy",
    )
    add(
        "R14",
        "Introducir intercalado",
        "Mezclar temas para mejorar discriminación y transferencia.",
        "strategy",
    )
    add(
        "R15",
        "Volver a práctica bloqueada",
        "Volver a práctica por bloques si el intercalado empeora el rendimiento.",
        "strategy",
    )
    add(
        "R16",
        "Cambiar tipo de actividad",
        "Cambiar formato de juego hacia el más eficaz para el alumno.",
        "strategy",
    )
    add(
        "R17",
        "Aumentar ejemplos concretos",
        "Añadir ejemplos guiados si hay errores conceptuales persistentes.",
        "strategy",
    )
    add(
        "R18",
        "Introducir variabilidad controlada",
        "Añadir variabilidad cuando hay dominio aparente pero baja transferencia.",
        "strategy",
    )
    add(
        "R19",
        "Añadir explicación tras error",
        "Mostrar explicación breve tras error cuando el mismo error se repite.",
        "strategy",
    )
    add(
        "R20",
        "Reducir explicación anticipada",
        "Evitar explicación previa excesiva cuando el alumno aprende bien por ensayo.",
        "strategy",
    )

    # Dosage (R21-R30)
    add(
        "R21",
        "Reducir duración de sesiones",
        "Acortar sesiones si hay fatiga intras sesión detectada.",
        "dosage",
    )
    add(
        "R22",
        "Aumentar sesiones cortas",
        "Aumentar frecuencia de sesiones breves si mejoran el rendimiento.",
        "dosage",
    )
    add(
        "R23",
        "Introducir descansos",
        "Insertar descansos si aumenta el abandono o baja la atención.",
        "dosage",
    )
    add(
        "R24",
        "Ajustar ritmo",
        "Ajustar ritmo de presentación según balance tiempo/accuracy.",
        "dosage",
    )
    add(
        "R25",
        "Añadir pausa reflexiva",
        "Añadir pausas si responde demasiado rápido con muchos errores.",
        "dosage",
    )
    add(
        "R26",
        "Aumentar automatización",
        "Aumentar práctica para reducir tiempo de respuesta manteniendo accuracy.",
        "dosage",
    )
    add(
        "R27",
        "Reducir volumen diario",
        "Reducir carga diaria si hay retroceso por exceso de volumen.",
        "dosage",
    )
    add(
        "R28",
        "Incrementar volumen",
        "Aumentar carga si hay dominio estable y margen de progreso.",
        "dosage",
    )
    add(
        "R29",
        "Ajustar dificultad",
        "Subir dificultad cuando el alumno se mantiene estable en alto rendimiento.",
        "dosage",
    )
    add(
        "R30",
        "Alternar días intensivos y ligeros",
        "Alternar intensidad para estabilizar rendimiento semanal.",
        "dosage",
    )

    # External validation (R31-R40)
    add(
        "R31",
        "Ejercicios tipo examen",
        "Introducir ejercicios tipo examen si hay discrepancia con nota real.",
        "external_validation",
    )
    add(
        "R32",
        "Revisar alineación temario",
        "Revisar si los ítems cubren el temario real evaluado.",
        "external_validation",
    )
    add(
        "R33",
        "Etiquetado por tutor",
        "Solicitar más contexto/etiquetado cuando la evaluación real es ambigua.",
        "external_validation",
    )
    add(
        "R34",
        "Reforzar transferencia",
        "Reforzar transferencia cuando falla en ítems nuevos pese a buen desempeño.",
        "external_validation",
    )
    add(
        "R35",
        "Priorizar conceptos clave del examen",
        "Priorizar conceptos marcados como clave por su peso evaluativo.",
        "external_validation",
    )
    add(
        "R36",
        "Reducir confianza excesiva",
        "Detectar falso dominio y ajustar cuando el examen contradice el desempeño.",
        "external_validation",
    )
    add(
        "R37",
        "Revisar consistencia entre sesiones",
        "Revisar variabilidad alta entre sesiones para evitar diagnósticos erróneos.",
        "external_validation",
    )
    add(
        "R38",
        "Activar revisión tutor–alumno",
        "Proponer revisión conjunta cuando hay señales contradictorias.",
        "external_validation",
    )
    add(
        "R39",
        "Mantener estrategia actual",
        "Mantener estrategia si hay mejora sostenida y consistente.",
        "external_validation",
    )
    add(
        "R40",
        "Reevaluar tras no mejora",
        "Reevaluar estrategia si no hay mejora tras ventana de evaluación.",
        "external_validation",
    )

    op.bulk_insert(recommendation_catalog, rows)


def downgrade() -> None:
    op.drop_table("recommendation_catalog")
