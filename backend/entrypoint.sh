#!/usr/bin/env sh
set -e

echo "Waiting for the database to accept connections..."
python <<'PY'
import sys
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

from app.config import settings

engine = create_engine(settings.database_url)
for attempt in range(1, 31):
    try:
        with engine.connect():
            print("Database is ready.")
            break
    except OperationalError as exc:
        print(f"Database not ready yet (attempt {attempt}/30): {exc}")
        time.sleep(2)
else:
    print("Database never became ready.", file=sys.stderr)
    sys.exit(1)
PY

echo "Running database migrations..."
alembic upgrade head

echo "Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
