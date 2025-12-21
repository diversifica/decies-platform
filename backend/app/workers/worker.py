from __future__ import annotations

import logging

from rq import Connection, Worker

from app.core.config import settings
from app.core.queue import _get_redis_connection

logger = logging.getLogger(__name__)


def main() -> None:
    redis_connection = _get_redis_connection()
    with Connection(redis_connection):
        worker = Worker([settings.RQ_QUEUE_NAME])
        worker.work()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
