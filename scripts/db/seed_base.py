"""
Seed the minimal catalog data needed for the DECIES platform without injecting
any sample content, microconcepts or uploads.

Use this after clearing the database (e.g. running
`scripts/db/clear_test_data.sql`) to reinsert:
  * Roles (alumno, tutor, admin, pipeline)
  * Activity types
  * Recommendation catalog entries
  * Default tutor / student / admin users (password: decies)

Run with:
  docker compose -f docker-compose.dev.yml exec backend python scripts/db/seed_base.py
"""

import uuid
from datetime import datetime

from sqlalchemy import select

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.models.activity import ActivityType
from app.models.recommendation_catalog import RecommendationCatalog
from app.models.role import Role
from app.models.tutor import Tutor
from app.models.user import User

ROLE_DEFINITIONS = [
    ("admin", "Admin Role"),
    ("student", "Student Role"),
    ("tutor", "Tutor Role"),
    ("Student", None),
    ("Tutor", None),
    ("Tutor_Pipeline", None),
]

ACTIVITY_TYPES = [
    ("QUIZ", "Quiz Interactivo"),
    ("EXAM_STYLE", "Modo Examen"),
    ("MATCH", "Emparejar Conceptos"),
    ("CLOZE", "Completar Huecos"),
    ("REVIEW", "Revisión Espaciada"),
]

RECOMMENDATION_CATALOG_ENTRIES = [
    ("R01", "Priorizar microconceptos en riesgo", "Enfocar práctica en microconceptos con dominio bajo y errores recurrentes.", "focus"),
    ("R02", "Consolidar microconceptos en progreso", "Aumentar práctica para microconceptos con dominio medio e inconsistencia.", "focus"),
    ("R03", "Repaso espaciado de microconceptos dominados", "Programar repasos para mantener retención en conceptos ya dominados.", "focus"),
    ("R04", "Reducir carga de nuevos conceptos", "Disminuir introducción de nuevo contenido si hay demasiados conceptos en riesgo.", "focus"),
    ("R05", "Reforzar prerequisitos", "Volver a prerequisitos cuando se detecten fallos base repetidos.", "focus"),
    ("R06", "Reorganizar orden del trimestre", "Reordenar el plan cuando la secuencia actual no es óptima para el alumno.", "focus"),
    ("R07", "Aumentar repetición inmediata tras errores", "Aplicar repetición inmediata para corregir errores persistentes.", "focus"),
    ("R08", "Introducir microevaluaciones frecuentes", "Usar comprobaciones cortas y frecuentes para detectar fallos pronto.", "focus"),
    ("R09", "Separar conceptos confundidos", "Desambiguar conceptos similares mediante práctica diferenciada.", "focus"),
    ("R10", "Simplificar dificultad temporalmente", "Bajar dificultad para recuperar confianza y evitar bloqueo.", "focus"),
    ("R11", "Aumentar recuperación sin ayudas", "Reducir dependencia de ayudas incrementando práctica de recuperación.", "strategy"),
    ("R12", "Limitar uso de pistas", "Limitar pistas si se detecta dependencia excesiva.", "strategy"),
    ("R13", "Sustituir repaso pasivo por práctica activa", "Reemplazar lectura/teoría por ejercicios de recuperación.", "strategy"),
    ("R14", "Introducir intercalado", "Mezclar temas para mejorar discriminación y transferencia.", "strategy"),
    ("R15", "Volver a práctica bloqueada", "Volver a práctica por bloques si el intercalado empeora el rendimiento.", "strategy"),
    ("R16", "Cambiar tipo de actividad", "Cambiar formato de juego hacia el más eficaz para el alumno.", "strategy"),
    ("R17", "Aumentar ejemplos concretos", "Añadir ejemplos guiados si hay errores conceptuales persistentes.", "strategy"),
    ("R18", "Introducir variabilidad controlada", "Añadir variabilidad cuando hay dominio aparente pero baja transferencia.", "strategy"),
    ("R19", "Añadir explicación tras error", "Mostrar explicación breve tras error cuando el mismo error se repite.", "strategy"),
    ("R20", "Reducir explicación anticipada", "Evitar explicación previa excesiva cuando el alumno aprende bien por ensayo.", "strategy"),
    ("R21", "Reducir duración de sesiones", "Acortar sesiones si hay fatiga intrasesión detectada.", "dosage"),
    ("R22", "Aumentar sesiones cortas", "Aumentar frecuencia de sesiones breves si mejoran el rendimiento.", "dosage"),
    ("R23", "Introducir descansos", "Insertar descansos si aumenta el abandono o baja la atención.", "dosage"),
    ("R24", "Ajustar ritmo", "Ajustar ritmo de presentación según balance tiempo/accuracy.", "dosage"),
    ("R25", "Añadir pausa reflexiva", "Añadir pausas si responde demasiado rápido con muchos errores.", "dosage"),
    ("R26", "Aumentar automatización", "Aumentar práctica para reducir tiempo de respuesta manteniendo accuracy.", "dosage"),
    ("R27", "Reducir volumen diario", "Reducir carga diaria si hay retroceso por exceso de volumen.", "dosage"),
    ("R28", "Incrementar volumen", "Aumentar carga si hay dominio estable y margen de progreso.", "dosage"),
    ("R29", "Ajustar dificultad", "Subir dificultad cuando el alumno se mantiene estable en alto rendimiento.", "dosage"),
    ("R30", "Alternar días intensivos y ligeros", "Alternar intensidad para estabilizar rendimiento semanal.", "dosage"),
    ("R31", "Ejercicios tipo examen", "Introducir ejercicios tipo examen si hay discrepancia con nota real.", "external_validation"),
    ("R32", "Revisar alineación temario", "Revisar si los ítems cubren el temario real evaluado.", "external_validation"),
    ("R33", "Etiquetado por tutor", "Solicitar más contexto/etiquetado cuando la evaluación real es ambigua.", "external_validation"),
    ("R34", "Reforzar transferencia", "Reforzar transferencia cuando falla en ítems nuevos pese a buen desempeño.", "external_validation"),
    ("R35", "Priorizar conceptos clave del examen", "Priorizar conceptos marcados como clave por su peso evaluativo.", "external_validation"),
    ("R36", "Reducir confianza excesiva", "Detectar falso dominio y ajustar cuando el examen contradice el desempeño.", "external_validation"),
    ("R37", "Revisar consistencia entre sesiones", "Revisar variabilidad alta entre sesiones para evitar diagnósticos erróneos.", "external_validation"),
    ("R38", "Activar revisión tutor–alumno", "Proponer revisión conjunta cuando hay señales contradictorias.", "external_validation"),
    ("R39", "Mantener estrategia actual", "Mantener estrategia si hay mejora sostenida y consistente.", "external_validation"),
    ("R40", "Reevaluar tras no mejora", "Reevaluar estrategia si no hay mejora tras ventana de evaluación.", "external_validation"),
]

DEFAULT_USERS = [
    ("admin@decies.com", "Admin Decies", "admin"),
    ("tutor@decies.com", "Profesor Decies", "tutor"),
    ("student@decies.com", "Alumno Decies", "student"),
]


def ensure_roles(session):
    for name, description in ROLE_DEFINITIONS:
        existing = session.scalar(select(Role).filter_by(name=name))
        if not existing:
            session.add(Role(id=uuid.uuid4(), name=name, description=description or name))


def ensure_activity_types(session):
    for code, name in ACTIVITY_TYPES:
        existing = session.scalar(select(ActivityType).filter_by(code=code))
        if not existing:
            session.add(ActivityType(id=uuid.uuid4(), code=code, name=name))


def ensure_recommendation_catalog(session):
    for code, title, description, category in RECOMMENDATION_CATALOG_ENTRIES:
        exists = session.scalar(select(RecommendationCatalog).filter_by(code=code))
        if exists:
            continue
        session.add(
            RecommendationCatalog(
                id=uuid.uuid4(),
                code=code,
                title=title,
                description=description,
                category=category,
                active=True,
                catalog_version="V1",
            )
        )


def ensure_default_users(session):
    default_password = "decies"
    for email, full_name, role_name in DEFAULT_USERS:
        role = session.scalar(select(Role).filter_by(name=role_name))
        if not role:
            raise SystemExit(f"Role {role_name} must exist before creating {email}")
        user = session.scalar(select(User).filter_by(email=email))
        if not user:
            user = User(
                id=uuid.uuid4(),
                email=email,
                hashed_password=get_password_hash(default_password),
                full_name=full_name,
                role_id=role.id,
                is_active=True,
            )
            session.add(user)
            session.flush()
        else:
            user.full_name = full_name
            user.role_id = role.id
            user.hashed_password = get_password_hash(default_password)
            user.is_active = True
        if role_name == "tutor":
            tutor = session.scalar(select(Tutor).filter_by(user_id=user.id))
            if not tutor:
                session.add(Tutor(id=uuid.uuid4(), user_id=user.id, display_name=full_name))
            else:
                tutor.display_name = full_name


def main():
    session = SessionLocal()
    try:
        session.begin()
        ensure_roles(session)
        ensure_activity_types(session)
        ensure_recommendation_catalog(session)
        ensure_default_users(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
