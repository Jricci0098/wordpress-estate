from datetime import UTC, datetime

from tests.integration.conftest import AGENT_ID, auth_headers


def _payload(request_id: str, site_name: str) -> dict:
    return {
        "schema_version": "inventory/v1",
        "agent_id": AGENT_ID,
        "request_id": request_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "host": {"hostname": "demo-host", "os_info": "Linux"},
        "sites": [
            {
                "site_name": site_name,
                "site_url": f"http://localhost/{site_name}",
                "wp_version": "6.6.2",
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


def _seed_five_sites(client):
    for i in range(1, 6):
        rid = f"req-page-{i}"
        client.post(
            "/api/v1/inventory", json=_payload(rid, f"wp{i}"), headers=auth_headers(rid)
        )


def test_sites_pagination_bounds(client):
    _seed_five_sites(client)

    page1 = client.get("/api/v1/sites?page=1&page_size=2").json()
    assert page1["total"] == 5
    assert len(page1["items"]) == 2
    assert page1["page"] == 1
    assert page1["page_size"] == 2

    page3 = client.get("/api/v1/sites?page=3&page_size=2").json()
    assert len(page3["items"]) == 1

    page_out_of_range = client.get("/api/v1/sites?page=99&page_size=2").json()
    assert page_out_of_range["items"] == []


def test_sites_pagination_rejects_invalid_params(client):
    resp = client.get("/api/v1/sites?page=0&page_size=2")
    assert resp.status_code == 422

    resp2 = client.get("/api/v1/sites?page=1&page_size=0")
    assert resp2.status_code == 422

    resp3 = client.get("/api/v1/sites?page=1&page_size=1000")
    assert resp3.status_code == 422


def test_plugins_pagination_bounds(client):
    _seed_five_sites(client)

    page1 = client.get("/api/v1/plugins?page=1&page_size=3").json()
    assert page1["total"] == 5
    assert len(page1["items"]) == 3
