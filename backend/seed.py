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
from app.models.game import Game
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

        role_admin = db.query(Role).filter_by(name="admin").first()
        if not role_admin:
            role_admin = Role(id=uuid.uuid4(), name="admin", description="Admin Role")
            db.add(role_admin)
            logger.info("Created Role: admin")

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
        elif not user_tutor.hashed_password.startswith("$pbkdf2-sha256$"):
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
        elif not user_student.hashed_password.startswith("$pbkdf2-sha256$"):
            user_student.hashed_password = get_password_hash(default_password)
            logger.info("Updated Student password hash")

        db.commit()

        # 3b. Create Admin User
        admin_email = "admin@decies.com"
        user_admin = db.query(User).filter_by(email=admin_email).first()
        if not user_admin:
            user_admin = User(
                id=uuid.uuid4(),
                email=admin_email,
                hashed_password=get_password_hash(default_password),
                full_name="Admin Decies",
                role_id=role_admin.id,
                is_active=True,
            )
            db.add(user_admin)
            logger.info(f"Created User: {admin_email}")
        elif not user_admin.hashed_password.startswith("$pbkdf2-sha256$"):
            user_admin.hashed_password = get_password_hash(default_password)
            logger.info("Updated Admin password hash")

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

        # Log the exact relationship for debugging
        logger.info("Student-Subject Relationship Debug:")
        logger.info(f"  Student ID: {student_profile.id}")
        logger.info(f"  Student user_id: {student_profile.user_id}")
        logger.info(f"  Student subject_id: {student_profile.subject_id}")
        logger.info(f"  Subject ID: {subject.id}")
        logger.info(f"  Subject tutor_id: {subject.tutor_id}")
        logger.info(f"  Tutor User ID: {user_tutor.id}")
        is_valid = student_profile.subject_id == subject.id and subject.tutor_id == user_tutor.id
        logger.info(f"  Relationship valid: {is_valid}")

        # 6. Create Activity Types (Day 4)
        activity_types_data = [
            ("QUIZ", "Quiz Interactivo"),
            ("EXAM_STYLE", "Modo Examen"),
            ("MATCH", "Emparejar Conceptos"),
            ("CLOZE", "Completar Huecos"),
            ("REVIEW", "Revisión Espaciada"),
        ]

        for code, name in activity_types_data:
            existing = db.query(ActivityType).filter_by(code=code).first()
            if not existing:
                activity_type = ActivityType(id=uuid.uuid4(), code=code, name=name, active=True)
                db.add(activity_type)
                logger.info(f"Created ActivityType: {code}")

        db.commit()

        # 6. Create Game configuration entries for pipeline
        game_templates = [
            {
                "code": "QUIZ",
                "name": "Quiz de opción múltiple",
                "description": (
                    "Items MCQ/Verdadero-Falso generados automáticamente por el pipeline LLM."
                ),
                "item_type": ItemType.MCQ,
                "prompt_template": (
                    "Usa E4/E5 para generar MCQ y VF fieles al contenido. Formato JSON: { ... }"
                ),
                "source_hint": "Prompt E4/E5",
                "active": True,
            },
            {
                "code": "MATCH",
                "name": "Juego de emparejamiento",
                "description": (
                    "Parejas de microconceptos y definiciones que refuerzan conexiones."
                ),
                "item_type": ItemType.MATCH,
                "prompt_template": (
                    "Genera pares left/right desde el contenido. Incluye explicaciones breves."
                ),
                "source_hint": "Prompt MATCH",
                "active": False,
            },
            {
                "code": "CLOZE",
                "name": "Completar huecos",
                "description": ("Oraciones con huecos para reforzar vocabulario clave."),
                "item_type": ItemType.CLOZE,
                "prompt_template": (
                    "Devuelve frases con placeholder y respuestas aceptables en JSON."
                ),
                "source_hint": "Prompt CLOZE",
                "active": False,
            },
        ]

        for data in game_templates:
            existing = db.query(Game).filter_by(code=data["code"]).first()
            if not existing:
                game = Game(
                    id=uuid.uuid4(),
                    code=data["code"],
                    name=data["name"],
                    description=data["description"],
                    item_type=data["item_type"],
                    prompt_template=data["prompt_template"],
                    prompt_version="V1",
                    engine_version="V1",
                    source_hint=data["source_hint"],
                    active=data["active"],
                )
                db.add(game)
                logger.info(f"Created Game: {game.code}")

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

        # 7.5. Create ContentUpload for seed items
        content_upload = db.query(ContentUpload).filter_by(file_name="sample_content.pdf").first()
        if not content_upload:
            content_upload = ContentUpload(
                id=uuid.uuid4(),
                tutor_id=tutor_profile.id,
                subject_id=subject.id,
                term_id=term.id,
                upload_type="pdf",
                storage_uri="seed/sample_content.pdf",
                file_name="sample_content.pdf",
                mime_type="application/pdf",
                page_count=10,
                processing_status="succeeded",
                processed_at=datetime.now(),
            )
            db.add(content_upload)
            logger.info("Created ContentUpload for seed items")

        db.commit()

        # 8. Create Sample Items
        # Get microconcepts for linking
        mc_001 = db.query(MicroConcept).filter_by(code="MC-001").first()
        mc_002 = db.query(MicroConcept).filter_by(code="MC-002").first()
        mc_003 = db.query(MicroConcept).filter_by(code="MC-003").first()
        mc_004 = db.query(MicroConcept).filter_by(code="MC-004").first()

        items_data = [
            # MCQ Items (3)
            {
                "type": ItemType.MCQ,
                "microconcept_id": mc_001.id if mc_001 else None,
                "stem": ("¿Cuál es el límite de f(x) = 1/x cuando x tiende a infinito?"),
                "options": {"choices": ["0", "1", "Infinito", "No existe"]},
                "correct_answer": "0",
                "explanation": ("Cuando x tiende a infinito, 1/x se aproxima a 0."),
                "source_game": "QUIZ",
            },
            {
                "type": ItemType.MCQ,
                "microconcept_id": mc_001.id if mc_001 else None,
                "stem": "¿Qué significa que una función sea continua en un punto?",
                "options": {
                    "choices": [
                        "El límite existe",
                        "El límite existe y es igual al valor de la función",
                        "La función está definida",
                        "La derivada existe",
                    ]
                },
                "correct_answer": ("El límite existe y es igual al valor de la función"),
                "explanation": (
                    "Una función es continua si el límite coincide con el valor de la función."
                ),
                "source_game": "QUIZ",
            },
            {
                "type": ItemType.MCQ,
                "microconcept_id": mc_001.id if mc_001 else None,
                "stem": "¿Cuál de las siguientes funciones NO es continua en x=0?",
                "options": {"choices": ["f(x) = x²", "f(x) = |x|", "f(x) = 1/x", "f(x) = sin(x)"]},
                "correct_answer": "f(x) = 1/x",
                "explanation": "f(x) = 1/x no está definida en x=0.",
                "source_game": "QUIZ",
            },
            # TRUE_FALSE Items (3)
            {
                "type": ItemType.TRUE_FALSE,
                "microconcept_id": mc_002.id if mc_002 else None,
                "stem": "La derivada de x² es 2x",
                "options": None,
                "correct_answer": "True",
                "explanation": "Aplicando la regla de potencias: d/dx(x²) = 2x.",
                "source_game": "QUIZ",
            },
            {
                "type": ItemType.TRUE_FALSE,
                "microconcept_id": mc_002.id if mc_002 else None,
                "stem": "La derivada de una constante es cero",
                "options": None,
                "correct_answer": "True",
                "explanation": "Las constantes no varían, por lo que su derivada es 0.",
                "source_game": "QUIZ",
            },
            {
                "type": ItemType.TRUE_FALSE,
                "microconcept_id": mc_002.id if mc_002 else None,
                "stem": "La derivada de sin(x) es cos(x)",
                "options": None,
                "correct_answer": "True",
                "explanation": "Es una de las derivadas trigonométricas básicas.",
                "source_game": "QUIZ",
            },
            # MATCH Items (3)
            {
                "type": ItemType.MATCH,
                "microconcept_id": mc_004.id if mc_004 else None,
                "stem": "Empareja cada operación con su propiedad",
                "options": {
                    "pairs": [
                        {"left": "A + B", "right": "Conmutativa"},
                        {"left": "A × B", "right": "No conmutativa"},
                        {"left": "det(A × B)", "right": "det(A) × det(B)"},
                    ]
                },
                "correct_answer": (
                    '{"A + B": "Conmutativa", "A × B": "No conmutativa", '
                    '"det(A × B)": "det(A) × det(B)"}'
                ),
                "explanation": ("La suma de matrices es conmutativa, pero el producto no."),
                "source_game": "MATCH",
            },
            {
                "type": ItemType.MATCH,
                "microconcept_id": mc_004.id if mc_004 else None,
                "stem": "Empareja cada matriz con su tipo",
                "options": {
                    "pairs": [
                        {"left": "[[1,0],[0,1]]", "right": "Identidad"},
                        {"left": "[[1,2],[2,1]]", "right": "Simétrica"},
                        {"left": "[[0,0],[0,0]]", "right": "Nula"},
                    ]
                },
                "correct_answer": (
                    '{"[[1,0],[0,1]]": "Identidad", '
                    '"[[1,2],[2,1]]": "Simétrica", "[[0,0],[0,0]]": "Nula"}'
                ),
                "explanation": "Cada matriz tiene propiedades específicas.",
                "source_game": "MATCH",
            },
            {
                "type": ItemType.MATCH,
                "microconcept_id": mc_004.id if mc_004 else None,
                "stem": "Empareja cada operación con su resultado",
                "options": {
                    "pairs": [
                        {"left": "det([[1,2],[3,4]])", "right": "-2"},
                        {"left": "det([[2,0],[0,3]])", "right": "6"},
                        {"left": "det([[1,1],[1,1]])", "right": "0"},
                    ]
                },
                "correct_answer": (
                    '{"det([[1,2],[3,4]])": "-2", "det([[2,0],[0,3]])": "6", '
                    '"det([[1,1],[1,1]])": "0"}'
                ),
                "explanation": "Cálculo de determinantes 2x2.",
                "source_game": "MATCH",
            },
            # CLOZE Items (3)
            {
                "type": ItemType.CLOZE,
                "microconcept_id": mc_003.id if mc_003 else None,
                "stem": "La integral de x dx es ___",
                "options": None,
                "correct_answer": '["x²/2 + C", "x^2/2 + C"]',
                "explanation": "Aplicando la regla de potencias para integrales.",
                "source_game": "CLOZE",
            },
            {
                "type": ItemType.CLOZE,
                "microconcept_id": mc_003.id if mc_003 else None,
                "stem": "La integral de cos(x) dx es ___",
                "options": None,
                "correct_answer": '["sin(x) + C"]',
                "explanation": "Integral trigonométrica básica.",
                "source_game": "CLOZE",
            },
            {
                "type": ItemType.CLOZE,
                "microconcept_id": mc_003.id if mc_003 else None,
                "stem": "La integral de 1/x dx es ___",
                "options": None,
                "correct_answer": '["ln|x| + C", "ln(|x|) + C"]',
                "explanation": "Integral logarítmica fundamental.",
                "source_game": "CLOZE",
            },
        ]

        for item_data in items_data:
            # Check if item already exists by stem
            existing_item = (
                db.query(Item)
                .filter_by(
                    stem=item_data["stem"],
                    content_upload_id=content_upload.id,
                )
                .first()
            )
            if not existing_item:
                item = Item(
                    id=uuid.uuid4(),
                    content_upload_id=content_upload.id,
                    microconcept_id=item_data["microconcept_id"],
                    type=item_data["type"],
                    stem=item_data["stem"],
                    options=item_data["options"],
                    correct_answer=item_data["correct_answer"],
                    explanation=item_data["explanation"],
                    difficulty=1,
                    validation_status="approved",
                    is_active=True,
                    source_game=item_data["source_game"],
                )
                db.add(item)
                logger.info(
                    f"Created Item ({item_data['type'].value}): {item_data['stem'][:50]}..."
                )

        db.commit()

        # 10. Link existing Items to MicroConcepts (Day 4)
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
