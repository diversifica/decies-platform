import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/login/access-token",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_subject_as_tutor():
    headers = _login("tutor@decies.com", "decies")
    name = f"Subject {uuid.uuid4().hex[:8]}"
    payload = {"name": name, "description": "Contenido educativo oficial"}

    response = client.post("/api/v1/catalog/subjects", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == name
    assert data["description"] == payload["description"]

    list_response = client.get("/api/v1/catalog/subjects", headers=headers)
    assert list_response.status_code == 200
    assert any(subject["id"] == data["id"] for subject in list_response.json())


def test_create_subject_requires_tutor():
    headers = _login("student@decies.com", "decies")
    payload = {"name": "Unauthorized materia"}

    response = client.post("/api/v1/catalog/subjects", json=payload, headers=headers)
    assert response.status_code == 403
