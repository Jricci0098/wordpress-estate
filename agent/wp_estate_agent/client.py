"""HTTP client for the estate backend. Read-only from the WordPress hosts'
point of view: this module only ever sends already-collected inventory data
and heartbeats. It never fetches or executes anything on the target hosts.
"""

import uuid
from datetime import UTC, datetime

import httpx


class EstateApiClient:
    def __init__(self, base_url: str, agent_id: str, agent_secret: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.agent_id = agent_id
        self.agent_secret = agent_secret
        self.timeout = timeout

    def _headers(self, request_id: str | None = None) -> dict:
        return {
            "X-Agent-Id": self.agent_id,
            "X-Agent-Secret": self.agent_secret,
            "X-Request-Id": request_id or str(uuid.uuid4()),
            "X-Request-Timestamp": datetime.now(UTC).isoformat(),
        }

    def heartbeat(self) -> httpx.Response:
        return httpx.post(
            f"{self.base_url}/api/v1/heartbeat", headers=self._headers(), timeout=self.timeout
        )

    def post_inventory(self, payload: dict) -> httpx.Response:
        """POST inventory with X-Request-Id aligned to payload["request_id"].

        The backend rejects inventory posts where the header and body
        request ids differ, and keys replay detection off this id, so the
        two must always match for a given payload (unlike heartbeat, which
        has no body and mints a fresh id per call).
        """
        return httpx.post(
            f"{self.base_url}/api/v1/inventory",
            headers=self._headers(request_id=str(payload["request_id"])),
            json=payload,
            timeout=self.timeout,
        )
