import copy
from datetime import UTC, datetime

from tests.integration.conftest import AGENT_ID, auth_headers

VARIED_PLUGINS = [
    {
        "slug": "akismet",
        "name": "Akismet",
        "version": "5.3",
        "path": "wp-content/plugins/akismet/akismet.php",
        "kind": "plugin",
        "origin": "wordpress_org",
        "status": "active",
        "update_status": "current",
    },
    {
        "slug": "acme-seo-pro",
        "name": "Acme SEO Pro",
        "version": "2.1",
        "path": "wp-content/plugins/acme-seo-pro/acme-seo-pro.php",
        "kind": "plugin",
        "origin": "commercial",
        "status": "active",
        "update_status": "unknown",
    },
    {
        "slug": "internal-billing-sync",
        "name": "Internal Billing Sync",
        "version": "0.4.0",
        "path": "wp-content/plugins/internal-billing-sync/internal-billing-sync.php",
        "kind": "plugin",
        "origin": "custom",
        "status": "active",
        "update_status": "unknown",
    },
    {
        "slug": "site-health-mu",
        "name": "Site Health MU Loader",
        "version": None,
        "path": "wp-content/mu-plugins/site-health-mu.php",
        "kind": "mu-plugin",
        "origin": "unknown",
        "status": "active",
        "update_status": "unknown",
    },
    {
        "slug": "object-cache",
        "name": "object-cache.php drop-in",
        "version": None,
        "path": "wp-content/object-cache.php",
        "kind": "dropin",
        "origin": "unknown",
        "status": "active",
        "update_status": "unknown",
    },
    {
        "slug": "mystery-plugin",
        "name": "Mystery Plugin",
        "version": "1.0",
        "path": "wp-content/plugins/mystery-plugin/mystery-plugin.php",
        "kind": "plugin",
        "origin": "unknown",
        "status": "unknown",
        "update_status": "unknown",
    },
]


def _payload(request_id: str) -> dict:
    return {
        "schema_version": "inventory/v1",
        "agent_id": AGENT_ID,
        "request_id": request_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "host": {"hostname": "demo-host", "os_info": "Linux"},
        "sites": [
            {
                "site_name": "wp1",
                "site_url": "http://localhost:8081",
                "wp_version": "6.6.2",
                "plugins": copy.deepcopy(VARIED_PLUGINS),
            }
        ],
    }


def test_commercial_and_custom_reject_current_status(client):
    bad = _payload("req-status-1")
    bad["sites"][0]["plugins"][1]["update_status"] = "current"
    resp = client.post("/api/v1/inventory", json=bad, headers=auth_headers("req-status-1"))
    assert resp.status_code == 422


def test_varied_plugin_sources_persist_distinctly(client):
    resp = client.post(
        "/api/v1/inventory", json=_payload("req-status-2"), headers=auth_headers("req-status-2")
    )
    assert resp.status_code == 201

    plugins = client.get("/api/v1/plugins?page=1&page_size=50").json()
    origins = {p["slug"]: p["origin"] for p in plugins["items"]}
    kinds = {p["slug"]: p["kind"] for p in plugins["items"]}
    assert origins["akismet"] == "wordpress_org"
    assert origins["acme-seo-pro"] == "commercial"
    assert origins["internal-billing-sync"] == "custom"
    assert kinds["site-health-mu"] == "mu-plugin"
    assert kinds["object-cache"] == "dropin"


def test_unknown_plugins_endpoint_lists_only_unknown_origin(client):
    client.post(
        "/api/v1/inventory", json=_payload("req-status-3"), headers=auth_headers("req-status-3")
    )

    unknown = client.get("/api/v1/plugins/unknown").json()
    slugs = {p["slug"] for p in unknown["items"]}
    assert slugs == {"site-health-mu", "object-cache", "mystery-plugin"}
    for item in unknown["items"]:
        assert item["origin"] == "unknown"
