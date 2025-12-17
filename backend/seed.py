import logging
import sys
import uuid
from datetime import datetime

# Add current directory to sys.path to resolve 'app' modules
sys.path.append(".")

from app.core.db import SessionLocal
from app.core.security import get_password_hash
from app.models.activity import ActivityType
from app.models.content import ContentUpload
from app.models.item import Item, ItemType
from app.models.microconcept import MicroConcept
from app.models.role import Role
from app.models.student import Student
from app.models.subject import Subject
from app.models.term import AcademicYear, Term
from app.models.tutor import Tutor
from app.models.user import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_db():
    default_password = "decies"

    db = SessionLocal()
    try:
        logger.info("Seeding database...")

        # 1. Create Roles
        role_tutor = db.query(Role).filter_by(name="tutor").first()
        if not role_tutor:
            role_tutor = Role(id=uuid.uuid4(), name="tutor", description="Tutor Role")
            db.add(role_tutor)
            logger.info("Created Role: tutor")

        role_student = db.query(Role).filter_by(name="student").first()
        if not role_student:
            role_student = Role(id=uuid.uuid4(), name="student", description="Student Role")
            db.add(role_student)
            logger.info("Created Role: student")

        db.commit()

        # 2. Create Tutor User
        tutor_email = "tutor@decies.com"
        user_tutor = db.query(User).filter_by(email=tutor_email).first()
        if not user_tutor:
            user_tutor = User(
                id=uuid.uuid4(),
                email=tutor_email,
                hashed_password=get_password_hash(default_password),
                full_name="Profesor Decies",
                role_id=role_tutor.id,
                is_active=True,
            )
            db.add(user_tutor)
            db.flush()  # Ensure user is pending insertion before tutor refers to it?
            logger.info(f"Created User: {tutor_email}")
        elif not user_tutor.hashed_password.startswith("$2"):
            user_tutor.hashed_password = get_password_hash(default_password)
            logger.info("Updated Tutor password hash")

        tutor_profile = db.query(Tutor).filter_by(user_id=user_tutor.id).first()
        if not tutor_profile:
            tutor_profile = Tutor(
                id=uuid.uuid4(), user_id=user_tutor.id, display_name="Profesor Decies (Ciencias)"
            )
            db.add(tutor_profile)
            logger.info("Created Tutor Profile")

        db.commit()

        # 3. Create Student User
        student_email = "student@decies.com"
        user_student = db.query(User).filter_by(email=student_email).first()
        if not user_student:
            user_student = User(
                id=uuid.uuid4(),
                email=student_email,
                hashed_password=get_password_hash(default_password),
                full_name="Alumno Decies",
                role_id=role_student.id,
                is_active=True,
            )
            db.add(user_student)
            logger.info(f"Created User: {student_email}")
        elif not user_student.hashed_password.startswith("$2"):
            user_student.hashed_password = get_password_hash(default_password)
            logger.info("Updated Student password hash")

        db.commit()

        # 4. Create Academic Year & Term
        year_name = "2025-2026"
        year = db.query(AcademicYear).filter_by(name=year_name).first()
        if not year:
            year = AcademicYear(
                id=uuid.uuid4(),
                name=year_name,
                start_date=datetime(2025, 9, 1),
                end_date=datetime(2026, 6, 30),
            )
            db.add(year)
            logger.info(f"Created AcademicYear: {year_name}")

        db.commit()  # Commit to get year ID if needed, though UUID generated locally

        term_name = "Trimestre 1"
        term = db.query(Term).filter_by(name=term_name).first()
        if not term:
            term = Term(
                id=uuid.uuid4(),
                name=term_name,
                code="T1",  # Added missing code
                academic_year_id=year.id,
            )
            db.add(term)
            logger.info(f"Created Term: {term_name}")

        db.commit()

        # 5. Create Subject
        subject_name = "Matemáticas Avanzadas"
        subject = db.query(Subject).filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(
                id=uuid.uuid4(),
                name=subject_name,
                description="Cálculo y Álgebra Lineal",
                tutor_id=user_tutor.id,
            )
            db.add(subject)
            logger.info(f"Created Subject: {subject.name}")

        db.commit()

        # 5b. Ensure Student Profile is linked to tutor subject
        student_profile = (
            db.query(Student)
            .filter((Student.user_id == user_student.id) | (Student.id == user_student.id))
            .first()
        )
        if not student_profile:
            student_profile = Student(
                id=user_student.id,
                user_id=user_student.id,
                subject_id=subject.id,
                enrollment_date=datetime.now(),
            )
            db.add(student_profile)
            logger.info("Created Student Profile")
        else:
            if not student_profile.user_id:
                student_profile.user_id = user_student.id
            if not student_profile.subject_id:
                student_profile.subject_id = subject.id
            db.add(student_profile)
            logger.info("Updated Student Profile links")

        db.commit()

        # 6. Create Activity Types (Day 4)
        activity_types_data = [
            ("QUIZ", "Quiz Interactivo"),
            ("MATCH", "Emparejar Conceptos"),
            ("REVIEW", "Revisión Espaciada"),
        ]

        for code, name in activity_types_data:
            existing = db.query(ActivityType).filter_by(code=code).first()
            if not existing:
                activity_type = ActivityType(id=uuid.uuid4(), code=code, name=name, active=True)
                db.add(activity_type)
                logger.info(f"Created ActivityType: {code}")

        db.commit()

        # 7. Create MicroConcepts (Day 4)
        microconcepts_data = [
            ("MC-001", "Límites de funciones", "Concepto de límite y continuidad"),
            ("MC-002", "Derivadas básicas", "Reglas de derivación elementales"),
            ("MC-003", "Integrales indefinidas", "Cálculo de primitivas"),
            ("MC-004", "Matrices y determinantes", "Operaciones con matrices"),
            ("MC-005", "Sistemas de ecuaciones lineales", "Resolución de sistemas"),
        ]

        for code, name, description in microconcepts_data:
            existing = db.query(MicroConcept).filter_by(code=code).first()
            if not existing:
                mc = MicroConcept(
                    id=uuid.uuid4(),
                    subject_id=subject.id,
                    term_id=term.id,
                    code=code,
                    name=name,
                    description=description,
                    active=True,
                )
                db.add(mc)
                logger.info(f"Created MicroConcept: {code} - {name}")

        db.commit()

        # 8. Link existing Items to MicroConcepts (Day 4)
        # Important: only link items to microconcepts that match the upload scope (subject/term).
        # Avoid cross-subject links that break mastery calculations.
        unlinked = (
            db.query(Item, ContentUpload)
            .join(ContentUpload, Item.content_upload_id == ContentUpload.id)
            .filter(Item.microconcept_id.is_(None))
            .all()
        )
        if unlinked:
            updated = 0
            for item, upload in unlinked:
                mc = (
                    db.query(MicroConcept)
                    .filter(
                        MicroConcept.subject_id == upload.subject_id,
                        MicroConcept.term_id == upload.term_id,
                        MicroConcept.active == True,  # noqa: E712
                    )
                    .order_by(MicroConcept.created_at.asc())
                    .first()
                )
                if not mc:
                    continue

                item.microconcept_id = mc.id
                updated += 1
                logger.info(f"Linked Item {item.id} to MicroConcept {mc.code or mc.name}")

            if updated:
                db.commit()

        # 9. Create test ContentUpload and Items for CI tests (Day 4)

        test_upload = db.query(ContentUpload).filter_by(file_name="test_upload.pdf").first()
        if not test_upload:
            tutor_profile = db.query(Tutor).filter_by(user_id=user_tutor.id).first()
            if not tutor_profile:
                logger.error("Tutor profile not found for test upload creation")
                return

            test_upload = ContentUpload(
                id=uuid.uuid4(),
                file_name="test_upload.pdf",
                storage_uri="/test/test_upload.pdf",
                mime_type="application/pdf",
                upload_type="pdf",
                tutor_id=tutor_profile.id,
                subject_id=subject.id,
                term_id=term.id,
            )
            db.add(test_upload)
            db.flush()
            logger.info("Created test ContentUpload")

            # Create test items
            first_mc = db.query(MicroConcept).filter_by(code="MC-001").first()
            for i in range(10):
                item = Item(
                    id=uuid.uuid4(),
                    content_upload_id=test_upload.id,
                    microconcept_id=first_mc.id if first_mc else None,
                    type=ItemType.MCQ,
                    stem=f"Pregunta de prueba {i + 1}",
                    options={"choices": ["Opción A", "Opción B", "Opción C", "Opción D"]},
                    correct_answer="Opción A",
                    explanation=f"Explicación de la pregunta {i + 1}",
                    difficulty=1,
                )
                db.add(item)
                logger.info(f"Created test Item {i + 1}")

            db.commit()

        logger.info("Seeding complete!")
        logger.info(f"Tutor User ID: {user_tutor.id}")
        logger.info(f"Tutor Profile ID: {tutor_profile.id}")
        logger.info(f"Student User ID: {user_student.id}")
        logger.info(f"Student Profile ID: {student_profile.id}")
        logger.info(f"Subject ID: {subject.id}")
        logger.info(f"Term ID: {term.id}")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
