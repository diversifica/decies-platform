from fastapi.testclient import TestClient

from app.main import app

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
    term_id = terms_res.json()[0]["id"]

    students_res = client.get(
        "/api/v1/catalog/students",
        headers=headers,
        params={"mine": "true", "subject_id": subject_id},
    )
    assert students_res.status_code == 200
    student_id = students_res.json()[0]["id"]

    response = client.get(
        f"/api/v1/metrics/students/{student_id}/metrics",
        params={"subject_id": subject_id, "term_id": term_id},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert "accuracy" in data
    assert "first_attempt_accuracy" in data
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
    term_id = terms_res.json()[0]["id"]

    students_res = client.get(
        "/api/v1/catalog/students",
        headers=headers,
        params={"mine": "true", "subject_id": subject_id},
    )
    assert students_res.status_code == 200
    student_id = students_res.json()[0]["id"]

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
    term_id = terms_res.json()[0]["id"]

    students_res = client.get(
        "/api/v1/catalog/students",
        headers=headers,
        params={"mine": "true", "subject_id": subject_id},
    )
    assert students_res.status_code == 200
    student_id = students_res.json()[0]["id"]

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
