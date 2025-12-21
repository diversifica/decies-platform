from __future__ import annotations

import uuid

import redis
from rq import Queue, Retry

from app.core.config import settings


def is_async_queue_enabled() -> bool:
    return bool(settings.ASYNC_QUEUE_ENABLED)


def _get_redis_connection() -> redis.Redis:
    return redis.from_url(settings.REDIS_URL)


def _get_queue() -> Queue:
    return Queue(
        name=settings.RQ_QUEUE_NAME,
        connection=_get_redis_connection(),
        default_timeout=int(settings.RQ_JOB_TIMEOUT_SECONDS),
    )


def enqueue_upload_processing(*, upload_id: uuid.UUID) -> str:
    queue = _get_queue()
    job = queue.enqueue(
        "app.tasks.process_upload_job",
        str(upload_id),
        retry=Retry(max=int(settings.RQ_JOB_RETRY_MAX)),
        job_timeout=int(settings.RQ_JOB_TIMEOUT_SECONDS),
    )
    return str(job.id)


def enqueue_recalculate_metrics(
    *,
    student_id: uuid.UUID,
    subject_id: uuid.UUID,
    term_id: uuid.UUID,
) -> str:
    queue = _get_queue()
    job = queue.enqueue(
        "app.tasks.recalculate_metrics_job",
        str(student_id),
        str(subject_id),
        str(term_id),
        retry=Retry(max=int(settings.RQ_JOB_RETRY_MAX)),
        job_timeout=int(settings.RQ_JOB_TIMEOUT_SECONDS),
    )
    return str(job.id)
