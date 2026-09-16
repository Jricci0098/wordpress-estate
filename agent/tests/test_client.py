import httpx
import respx

from wp_estate_agent.client import EstateApiClient

BASE_URL = "http://backend.local"


@respx.mock
def test_heartbeat_sends_expected_auth_headers():
    route = respx.post(f"{BASE_URL}/api/v1/heartbeat").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = EstateApiClient(base_url=BASE_URL, agent_id="agent-1", agent_secret="s3cr3t")

    resp = client.heartbeat()

    assert resp.status_code == 200
    assert route.called
    sent_headers = route.calls[0].request.headers
    assert sent_headers["x-agent-id"] == "agent-1"
    assert sent_headers["x-agent-secret"] == "s3cr3t"
    assert sent_headers["x-request-id"]
    assert sent_headers["x-request-timestamp"]


@respx.mock
def test_post_inventory_sends_payload_as_json_body():
    route = respx.post(f"{BASE_URL}/api/v1/inventory").mock(
        return_value=httpx.Response(201, json={"sites_processed": 1})
    )
    client = EstateApiClient(base_url=BASE_URL, agent_id="agent-1", agent_secret="s3cr3t")
    payload = {"schema_version": "inventory/v1", "request_id": "req-body-1", "sites": []}

    resp = client.post_inventory(payload)

    assert resp.status_code == 201
    assert route.called
    assert route.calls[0].request.content


@respx.mock
def test_each_heartbeat_gets_a_distinct_request_id():
    respx.post(f"{BASE_URL}/api/v1/heartbeat").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    client = EstateApiClient(base_url=BASE_URL, agent_id="agent-1", agent_secret="s3cr3t")

    client.heartbeat()
    client.heartbeat()

    ids = [c.request.headers["x-request-id"] for c in respx.calls]
    assert ids[0] != ids[1]


@respx.mock
def test_post_inventory_uses_payload_request_id_as_header():
    """The backend rejects an inventory post if X-Request-Id doesn't match
    payload.request_id, so the production client must align the two rather
    than minting its own random header id (as heartbeat does).
    """
    route = respx.post(f"{BASE_URL}/api/v1/inventory").mock(
        return_value=httpx.Response(201, json={"sites_processed": 1})
    )
    client = EstateApiClient(base_url=BASE_URL, agent_id="agent-1", agent_secret="s3cr3t")
    payload = {"schema_version": "inventory/v1", "request_id": "fixed-request-id-42", "sites": []}

    client.post_inventory(payload)

    assert route.called
    sent_headers = route.calls[0].request.headers
    assert sent_headers["x-request-id"] == "fixed-request-id-42"


@respx.mock
def test_post_inventory_replay_is_rejected_by_backend():
    """Replaying the exact same payload through the real client must reuse
    the same X-Request-Id (since it's derived from payload.request_id), so
    the backend's replay protection actually has something to key off of.
    """
    route = respx.post(f"{BASE_URL}/api/v1/inventory").mock(
        side_effect=[
            httpx.Response(201, json={"sites_processed": 1}),
            httpx.Response(409, json={"detail": "duplicate request id (replay detected)"}),
        ]
    )
    client = EstateApiClient(base_url=BASE_URL, agent_id="agent-1", agent_secret="s3cr3t")
    payload = {"schema_version": "inventory/v1", "request_id": "replayed-request-id", "sites": []}

    first = client.post_inventory(payload)
    second = client.post_inventory(payload)

    assert first.status_code == 201
    assert second.status_code == 409
    ids = [c.request.headers["x-request-id"] for c in route.calls]
    assert ids[0] == ids[1] == "replayed-request-id"
