import uuid

from fastapi.testclient import TestClient

from app.core.db import SessionLocal
from app.main import app
from app.models.student import Student

client = TestClient(app)


def _login(email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/login/access-token",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_assign_subject_to_student():
    headers = _login("tutor@decies.com", "decies")
    subject_name = f"Subject {uuid.uuid4().hex[:8]}"
    payload = {"name": subject_name, "description": "Asignatura temporal"}

    response = client.post("/api/v1/catalog/subjects", json=payload, headers=headers)
    assert response.status_code == 201
    created = response.json()

    students_res = client.get("/api/v1/catalog/students", headers=headers, params={"mine": "true"})
    assert students_res.status_code == 200
    student = students_res.json()[0]

    assign_res = client.patch(
        f"/api/v1/catalog/students/{student['id']}",
        json={"subject_id": created["id"]},
        headers=headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["subject_id"] == created["id"]

    post_assign = client.get(
        "/api/v1/catalog/students",
        headers=headers,
        params={"mine": "true", "subject_id": created["id"]},
    )
    assert post_assign.status_code == 200
    assert any(item["id"] == student["id"] for item in post_assign.json())


def test_assign_subject_requires_tutor():
    tutor_headers = _login("tutor@decies.com", "decies")
    students_res = client.get("/api/v1/catalog/students", headers=tutor_headers, params={"mine": "true"})
    assert students_res.status_code == 200
    student = students_res.json()[0]

    subjects_res = client.get("/api/v1/catalog/subjects", headers=tutor_headers, params={"mine": "true"})
    assert subjects_res.status_code == 200
    subject_id = subjects_res.json()[0]["id"]

    student_headers = _login("student@decies.com", "decies")
    response = client.patch(
        f"/api/v1/catalog/students/{student['id']}",
        json={"subject_id": subject_id},
        headers=student_headers,
    )
    assert response.status_code == 403


def test_force_delete_subject_with_dependencies():
    headers = _login("tutor@decies.com", "decies")
    payload = {"name": f"Subject {uuid.uuid4().hex[:6]}", "description": "Temporal con dependencias"}

    response = client.post("/api/v1/catalog/subjects", json=payload, headers=headers)
    assert response.status_code == 201
    created = response.json()

    extra_student = Student(id=uuid.uuid4(), subject_id=created["id"])
    extra_student_id = extra_student.id
    with SessionLocal() as db:
        db.add(extra_student)
        db.commit()

    delete_response = client.delete(f"/api/v1/catalog/subjects/{created['id']}", headers=headers)
    assert delete_response.status_code == 409

    force_response = client.delete(
        f"/api/v1/catalog/subjects/{created['id']}?force=true",
        headers=headers,
    )
    assert force_response.status_code == 204

    with SessionLocal() as db:
        db.query(Student).filter(Student.id == extra_student_id).delete()
        db.commit()
