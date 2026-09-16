"""Minimal real queue worker for the WordPress Estate MVP.

This worker connects to Redis and consumes jobs from a list-based queue with
BLPOP. It intentionally does not execute any update/remediation logic: the
estate platform is read-only for this MVP (see IMPLEMENTATION_BRIEF.md), so
this process exists only to prove a real queue consumer is wired up and
healthy. Nothing here shells out or mutates a WordPress site.
"""

import json
import logging
import os
import signal
import time
from types import FrameType

import redis

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("wp-estate-worker")

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
QUEUE_KEY = os.environ.get("WORKER_QUEUE_KEY", "estate:jobs")
HEALTH_FILE = os.environ.get("WORKER_HEALTH_FILE", "/tmp/worker-healthy")

_running = True


def _handle_shutdown(signum: int, _frame: FrameType | None) -> None:
    global _running
    log.info("received signal %s, shutting down", signum)
    _running = False


def main() -> None:
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    client = redis.Redis.from_url(REDIS_URL)
    log.info("worker started; watching queue '%s' on %s", QUEUE_KEY, REDIS_URL)

    while _running:
        try:
            client.ping()
            with open(HEALTH_FILE, "w") as fh:
                fh.write(str(time.time()))
        except redis.RedisError:
            log.exception("redis ping failed")
            time.sleep(2)
            continue

        item = client.blpop(QUEUE_KEY, timeout=5)
        if item is None:
            continue

        _, raw = item
        try:
            job = json.loads(raw)
        except json.JSONDecodeError:
            log.warning("dropping unparsable job payload: %r", raw)
            continue

        log.info("received job (no-op, read-only MVP): %s", job)

    log.info("worker stopped")


if __name__ == "__main__":
    main()
