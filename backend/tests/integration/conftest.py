from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import hash_secret
from app.db import Base, get_db
from app.main import app
from app.models import Agent

AGENT_ID = "agent-integration"
AGENT_SECRET = "integration-secret"


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture()
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture()
def client(engine, session_factory):
    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db

    seed_db = session_factory()
    seed_db.add(Agent(id=AGENT_ID, secret_hash=hash_secret(AGENT_SECRET)))
    seed_db.commit()
    seed_db.close()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def auth_headers(request_id: str, agent_id: str = AGENT_ID, secret: str = AGENT_SECRET) -> dict:
    return {
        "X-Agent-Id": agent_id,
        "X-Agent-Secret": secret,
        "X-Request-Id": request_id,
        "X-Request-Timestamp": datetime.now(UTC).isoformat(),
    }
