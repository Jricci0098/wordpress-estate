import csv
import io
from datetime import UTC, datetime

from tests.integration.conftest import AGENT_ID, auth_headers


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


def test_csv_export_contains_plugin_rows(client):
    client.post("/api/v1/inventory", json=_payload("req-csv"), headers=auth_headers("req-csv"))

    resp = client.get("/api/v1/export/plugins.csv")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/csv")

    body = resp.text
    assert "slug" in body.splitlines()[0]
    assert "akismet" in body
    assert "wp1" in body


def _payload_with_formula_fields(request_id: str) -> dict:
    payload = _payload(request_id)
    payload["sites"][0]["site_name"] = "=cmd|' /C calc'!A1"
    plugin = payload["sites"][0]["plugins"][0]
    plugin["slug"] = "+HYPERLINK(\"http://evil.example\")"
    plugin["name"] = "-2+3"
    plugin["path"] = "@SUM(1,1)"
    return payload


def test_csv_export_sanitizes_formula_injection(client):
    client.post(
        "/api/v1/inventory",
        json=_payload_with_formula_fields("req-csv-formula"),
        headers=auth_headers("req-csv-formula"),
    )

    resp = client.get("/api/v1/export/plugins.csv")
    assert resp.status_code == 200

    rows = list(csv.reader(io.StringIO(resp.text)))
    header, row = rows[0], rows[1]
    fields = dict(zip(header, row, strict=True))

    for field in ("site_name", "slug", "name", "path"):
        value = fields[field]
        assert not value.startswith(("=", "+", "-", "@")), f"{field}={value!r} not sanitized"
        assert value.startswith("'"), f"{field}={value!r} missing sanitization prefix"
