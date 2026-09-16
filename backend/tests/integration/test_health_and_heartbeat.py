from tests.integration.conftest import auth_headers


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_heartbeat_requires_valid_auth(client):
    resp = client.post("/api/v1/heartbeat", headers=auth_headers("hb-1"))
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_heartbeat_rejects_replay(client):
    client.post("/api/v1/heartbeat", headers=auth_headers("hb-dup"))
    resp = client.post("/api/v1/heartbeat", headers=auth_headers("hb-dup"))
    assert resp.status_code == 409
