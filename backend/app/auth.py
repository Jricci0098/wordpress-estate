"""Per-agent authentication with replay resistance.

Agents authenticate with a shared secret (stored server-side only as a
salted hash) plus a request id + timestamp pair. The timestamp must be
within a freshness window and the (agent_id, request_id) pair must never
have been seen before, which is enforced with a unique constraint.
"""

import hashlib
import hmac
import os
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.models import Agent, AgentRequestLog

_HASH_ITERATIONS = 200_000


def hash_secret(secret: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", secret.encode(), salt, _HASH_ITERATIONS)
    return f"{salt.hex()}${derived.hex()}"


def verify_secret(secret: str, secret_hash: str) -> bool:
    try:
        salt_hex, _ = secret_hash.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    candidate = hash_secret(secret, salt=salt)
    return hmac.compare_digest(candidate, secret_hash)


def _parse_timestamp(raw: str) -> datetime:
    try:
        ts = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid request timestamp") from exc
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts


def require_agent_auth(endpoint: str) -> Callable[..., Agent]:
    """Build a FastAPI dependency that authenticates an agent for ``endpoint``."""

    def _dependency(
        x_agent_id: str = Header(...),
        x_agent_secret: str = Header(...),
        x_request_id: str = Header(...),
        x_request_timestamp: str = Header(...),
        db: Session = Depends(get_db),
    ) -> Agent:
        agent = db.get(Agent, x_agent_id)
        if agent is None or not verify_secret(x_agent_secret, agent.secret_hash):
            raise HTTPException(status_code=401, detail="invalid agent credentials")

        ts = _parse_timestamp(x_request_timestamp)
        now = datetime.now(UTC)
        skew = abs((now - ts).total_seconds())
        if skew > settings.replay_freshness_seconds:
            raise HTTPException(status_code=401, detail="stale request timestamp")

        db.add(AgentRequestLog(agent_id=agent.id, request_id=x_request_id, endpoint=endpoint))
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=409, detail="duplicate request id (replay detected)"
            ) from None

        agent.last_seen_at = now
        db.commit()
        return agent

    return _dependency
