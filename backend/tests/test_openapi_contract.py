from app.main import app


def test_openapi_contract_basics():
    spec = app.openapi()

    assert spec["openapi"].startswith("3.")
    assert spec["info"]["title"] == "DECIES API"
    assert spec["info"]["version"] == "0.1.0"

    paths = spec.get("paths", {})
    required = [
        "/health",
        "/api/v1/auth/me",
        "/api/v1/activities/sessions",
        "/api/v1/recommendations/students/{student_id}",
        "/api/v1/reports/students/{student_id}/generate",
    ]

    missing = [path for path in required if path not in paths]
    assert not missing, f"Missing OpenAPI paths: {missing}"
