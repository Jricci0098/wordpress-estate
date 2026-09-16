from datetime import UTC, datetime

from tests.integration.conftest import AGENT_ID, auth_headers


def _payload(request_id: str, site_name: str = "wp1", wp_version: str = "6.6.2") -> dict:
    return {
        "schema_version": "inventory/v1",
        "agent_id": AGENT_ID,
        "request_id": request_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "host": {"hostname": "demo-host", "os_info": "Linux"},
        "sites": [
            {
                "site_name": site_name,
                "site_url": "http://localhost:8081",
                "wp_version": wp_version,
                "plugins": [
                    {
                        "slug": "akismet",
                        "name": "Akismet",
                        "version": "5.3",
                        "path": "wp-content/plugins/akismet/akismet.php",
                        "kind": "plugin",
                        "origin": "wordpress_org",
                        "status": "active",
                        "update_status": "current",
                    }
                ],
            }
        ],
    }


def test_ingest_creates_site_and_snapshot(client):
    resp = client.post(
        "/api/v1/inventory", json=_payload("req-a"), headers=auth_headers("req-a")
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["sites_processed"] == 1

    sites = client.get("/api/v1/sites").json()
    assert sites["total"] == 1
    assert sites["items"][0]["name"] == "wp1"
    assert sites["items"][0]["wp_version"] == "6.6.2"


def test_snapshots_are_append_only(client):
    client.post("/api/v1/inventory", json=_payload("req-b1"), headers=auth_headers("req-b1"))
    client.post(
        "/api/v1/inventory",
        json=_payload("req-b2", wp_version="6.6.3"),
        headers=auth_headers("req-b2"),
    )

    sites = client.get("/api/v1/sites").json()
    assert sites["total"] == 1
    assert sites["items"][0]["wp_version"] == "6.6.3"
    assert sites["items"][0]["snapshot_count"] == 2


def test_duplicate_request_id_is_rejected(client):
    resp1 = client.post(
        "/api/v1/inventory", json=_payload("req-dup"), headers=auth_headers("req-dup")
    )
    assert resp1.status_code == 201

    resp2 = client.post(
        "/api/v1/inventory", json=_payload("req-dup"), headers=auth_headers("req-dup")
    )
    assert resp2.status_code == 409

    sites = client.get("/api/v1/sites").json()
    assert sites["items"][0]["snapshot_count"] == 1


def test_unsupported_schema_version_rejected(client):
    bad = _payload("req-c")
    bad["schema_version"] = "inventory/v2"
    resp = client.post("/api/v1/inventory", json=bad, headers=auth_headers("req-c"))
    assert resp.status_code == 422


def test_invalid_secret_rejected(client):
    resp = client.post(
        "/api/v1/inventory",
        json=_payload("req-d"),
        headers=auth_headers("req-d", secret="wrong"),
    )
    assert resp.status_code == 401


def test_request_id_header_body_mismatch_is_rejected(client):
    resp = client.post(
        "/api/v1/inventory",
        json=_payload("body-request-id"),
        headers=auth_headers("header-request-id"),
    )
    assert resp.status_code == 400

    sites = client.get("/api/v1/sites").json()
    assert sites["total"] == 0
