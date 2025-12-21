import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _login(email: str, password: str) -> dict[str, str]:
    token_res = client.post(
        "/api/v1/login/access-token",
        json={"email": email, "password": password},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_admin_endpoints_rbac_list_catalog_and_items():
    admin_headers = _login("admin@decies.com", "decies")
    tutor_headers = _login("tutor@decies.com", "decies")
    student_headers = _login("student@decies.com", "decies")

    res = client.get("/api/v1/admin/recommendation-catalog", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res = client.get("/api/v1/admin/recommendation-catalog", headers=tutor_headers)
    assert res.status_code == 403

    res = client.get("/api/v1/admin/recommendation-catalog", headers=student_headers)
    assert res.status_code == 403

    res = client.get("/api/v1/admin/items", headers=admin_headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_admin_endpoints_rbac_patch_catalog():
    admin_headers = _login("admin@decies.com", "decies")
    tutor_headers = _login("tutor@decies.com", "decies")

    catalog = client.get("/api/v1/admin/recommendation-catalog", headers=admin_headers).json()
    assert catalog
    code = catalog[0]["code"]

    res = client.patch(
        f"/api/v1/admin/recommendation-catalog/{code}",
        headers=admin_headers,
        json={"active": catalog[0]["active"]},
    )
    assert res.status_code == 200
    assert res.json()["code"] == code

    res = client.patch(
        f"/api/v1/admin/recommendation-catalog/{code}",
        headers=tutor_headers,
        json={"active": catalog[0]["active"]},
    )
    assert res.status_code == 403


def test_admin_endpoints_rbac_patch_activity_type():
    admin_headers = _login("admin@decies.com", "decies")
    tutor_headers = _login("tutor@decies.com", "decies")

    types = client.get("/api/v1/admin/activity-types", headers=admin_headers).json()
    assert types
    activity_type_id = uuid.UUID(types[0]["id"])

    res = client.patch(
        f"/api/v1/admin/activity-types/{activity_type_id}",
        headers=admin_headers,
        json={"active": types[0]["active"]},
    )
    assert res.status_code == 200

    res = client.patch(
        f"/api/v1/admin/activity-types/{activity_type_id}",
        headers=tutor_headers,
        json={"active": types[0]["active"]},
    )
    assert res.status_code == 403
