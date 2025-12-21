from __future__ import annotations

import logging

from rq import Worker

from app.core.config import settings
from app.core.queue import _get_redis_connection

logger = logging.getLogger(__name__)


def main() -> None:
    redis_connection = _get_redis_connection()
    worker = Worker([settings.RQ_QUEUE_NAME], connection=redis_connection)
    worker.work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
