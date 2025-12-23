from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
from app.models.student import Student
from app.models.user import User

client = TestClient(app)


def _login(email: str, password: str) -> dict[str, str]:
    token_res = client.post(
        "/api/v1/login/access-token", json={"email": email, "password": password}
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_student_metrics():
    """Test getting student metrics"""
    headers = _login("tutor@decies.com", "decies")

    subjects_res = client.get("/api/v1/catalog/subjects", headers=headers, params={"mine": "true"})
    assert subjects_res.status_code == 200
    subject_id = subjects_res.json()[0]["id"]

    terms_res = client.get("/api/v1/catalog/terms", headers=headers, params={"active": "true"})
    assert terms_res.status_code == 200
    assert "academic_year_name" in terms_res.json()[0]
    term_id = terms_res.json()[0]["id"]

    # Get student directly from database (workaround for catalog/students endpoint issue)
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(subject_id=subject_id).first()
        assert student is not None, "No student found for subject"
        student_id = str(student.id)
    finally:
        db.close()

    response = client.get(
        f"/api/v1/metrics/students/{student_id}/metrics",
        params={"subject_id": subject_id, "term_id": term_id},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "first_attempt_accuracy" in data
    assert "error_rate" in data
    assert "performance_consistency" in data
    assert "median_response_time_ms" in data
    assert "total_sessions" in data
    assert data["student_id"] == student_id


def test_get_mastery_states():
    """Test getting mastery states for a student"""
    headers = _login("tutor@decies.com", "decies")

    subjects_res = client.get("/api/v1/catalog/subjects", headers=headers, params={"mine": "true"})
    assert subjects_res.status_code == 200
    subject_id = subjects_res.json()[0]["id"]

    terms_res = client.get("/api/v1/catalog/terms", headers=headers, params={"active": "true"})
    assert terms_res.status_code == 200
    assert "academic_year_name" in terms_res.json()[0]
    term_id = terms_res.json()[0]["id"]

    # Get student directly from database (workaround for catalog/students endpoint issue)
    db = SessionLocal()
    try:
        student = db.query(Student).filter_by(subject_id=subject_id).first()
        assert student is not None, "No student found for subject"
        student_id = str(student.id)
    finally:
        db.close()

    response = client.get(
        f"/api/v1/metrics/students/{student_id}/mastery",
        params={"subject_id": subject_id, "term_id": term_id},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

    # Should have mastery states for all microconcepts
    if len(data) > 0:
        state = data[0]
        assert "microconcept_id" in state
        assert "microconcept_name" in state
        assert "mastery_score" in state
        assert "status" in state
        assert state["status"] in ["dominant", "in_progress", "at_risk"]


def test_recalculate_metrics():
    """Test manual metrics recalculation"""
    headers = _login("tutor@decies.com", "decies")

    subjects_res = client.get("/api/v1/catalog/subjects", headers=headers, params={"mine": "true"})
    assert subjects_res.status_code == 200
    subject_id = subjects_res.json()[0]["id"]

    terms_res = client.get("/api/v1/catalog/terms", headers=headers, params={"active": "true"})
    assert terms_res.status_code == 200
    assert "academic_year_name" in terms_res.json()[0]
    term_id = terms_res.json()[0]["id"]

    # Get student directly from database by email (workaround for catalog/students endpoint issue)
    db = SessionLocal()
    try:
        user = db.query(User).filter_by(email="student@decies.com").first()
        assert user is not None, "Student user not found"
        student = db.query(Student).filter_by(user_id=user.id).first()
        assert student is not None, "Student profile not found"
        student_id = str(student.id)
    finally:
        db.close()

    response = client.post(
        "/api/v1/metrics/recalculate",
        params={
            "student_id": student_id,
            "subject_id": subject_id,
            "term_id": term_id,
        },
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "metrics_id" in data
    assert "mastery_states_count" in data
