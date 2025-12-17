from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_login_and_me_and_catalog():
    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": "tutor@decies.com", "password": "decies"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    me = me_res.json()
    assert me["email"] == "tutor@decies.com"
    assert me["tutor_id"] is not None

    subjects_res = client.get("/api/v1/catalog/subjects", headers=headers, params={"mine": "true"})
    assert subjects_res.status_code == 200
    assert len(subjects_res.json()) >= 1

    terms_res = client.get("/api/v1/catalog/terms", headers=headers, params={"active": "true"})
    assert terms_res.status_code == 200
    assert len(terms_res.json()) >= 1

    students_res = client.get("/api/v1/catalog/students", headers=headers, params={"mine": "true"})
    assert students_res.status_code == 200
    assert len(students_res.json()) >= 1
