import uuid

import pytest
import redis
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.queue import enqueue_upload_processing
from app.main import app


def _redis_ping() -> None:
    connection = redis.from_url(settings.REDIS_URL)
    connection.ping()


def test_health_redis_ok() -> None:
    try:
        _redis_ping()
    except redis.exceptions.RedisError:
        pytest.skip("Redis not available")

    client = TestClient(app)
    response = client.get("/health/redis")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["redis"] == "ok"


def test_enqueue_upload_processing_returns_job_id() -> None:
    try:
        _redis_ping()
    except redis.exceptions.RedisError:
        pytest.skip("Redis not available")

    job_id = enqueue_upload_processing(upload_id=uuid.uuid4())
    assert job_id
