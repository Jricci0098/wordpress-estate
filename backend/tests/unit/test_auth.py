from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException

from app.auth import hash_secret, require_agent_auth
from app.models import Agent

AGENT_ID = "agent-demo"
SECRET = "correct-horse-battery-staple"


@pytest.fixture()
def agent(db_session):
    agent = Agent(id=AGENT_ID, secret_hash=hash_secret(SECRET))
    db_session.add(agent)
    db_session.commit()
    return agent


def _call(db_session, *, agent_id=AGENT_ID, secret=SECRET, request_id="req-1", timestamp=None):
    ts = timestamp or datetime.now(UTC).isoformat()
    dep = require_agent_auth("heartbeat")
    return dep(
        x_agent_id=agent_id,
        x_agent_secret=secret,
        x_request_id=request_id,
        x_request_timestamp=ts,
        db=db_session,
    )


def test_valid_agent_auth_succeeds(db_session, agent):
    result = _call(db_session)
    assert result.id == AGENT_ID


def test_invalid_secret_rejected(db_session, agent):
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, secret="wrong-secret")
    assert exc_info.value.status_code == 401


def test_unknown_agent_rejected(db_session, agent):
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, agent_id="no-such-agent")
    assert exc_info.value.status_code == 401


def test_stale_timestamp_rejected(db_session, agent):
    stale = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, timestamp=stale)
    assert exc_info.value.status_code == 401


def test_duplicate_request_id_rejected(db_session, agent):
    _call(db_session, request_id="req-dup")
    with pytest.raises(HTTPException) as exc_info:
        _call(db_session, request_id="req-dup")
    assert exc_info.value.status_code == 409
