import logging
import sys
import uuid
from datetime import datetime
from sqlalchemy.orm import Session

# Add current directory to sys.path to resolve 'app' modules
sys.path.append(".")

from app.core.db import SessionLocal, engine
from app.models.role import Role
from app.models.user import User
from app.models.tutor import Tutor
from app.models.student import Student
from app.models.term import AcademicYear, Term
from app.models.subject import Subject

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_db():
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
                hashed_password="hashed_secret_password", # Dummy hash
                full_name="Profesor Decies",
                role_id=role_tutor.id,
                is_active=True
            )
            db.add(user_tutor)
            db.flush() # Ensure user is pending insertion before tutor refers to it?
            logger.info(f"Created User: {tutor_email}")
            
            # Create Tutor Profile
            tutor_profile = Tutor(
                id=uuid.uuid4(),
                user_id=user_tutor.id,
                display_name="Profesor Decies (Ciencias)"
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
                hashed_password="hashed_secret_password",
                full_name="Alumno Decies",
                role_id=role_student.id,
                is_active=True
            )
            db.add(user_student)
            logger.info(f"Created User: {student_email}")
            
            # Create Student Profile
            student_profile = Student(id=user_student.id, enrollment_date=datetime.now())
            db.add(student_profile)
            logger.info("Created Student Profile")

        db.commit()

        # 4. Create Academic Year & Term
        year_name = "2025-2026"
        year = db.query(AcademicYear).filter_by(name=year_name).first()
        if not year:
            year = AcademicYear(id=uuid.uuid4(), name=year_name, start_date=datetime(2025, 9, 1), end_date=datetime(2026, 6, 30))
            db.add(year)
            logger.info(f"Created AcademicYear: {year_name}")
        
        db.commit() # Commit to get year ID if needed, though UUID generated locally

        term_name = "Trimestre 1"
        term = db.query(Term).filter_by(name=term_name).first()
        if not term:
            term = Term(
                id=uuid.uuid4(),
                name=term_name,
                code="T1", # Added missing code
                academic_year_id=year.id,
                start_date=datetime(2025, 9, 1),
                end_date=datetime(2025, 12, 20)
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
                tutor_id=user_tutor.id
            )
            db.add(subject)
            logger.info(f"Created Subject: {subject.name}")

        db.commit()
        
        logger.info("Seeding complete!")

    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
