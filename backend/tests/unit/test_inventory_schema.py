from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.inventory import InventoryPayload

VALID_PAYLOAD = {
    "schema_version": "inventory/v1",
    "agent_id": "agent-demo",
    "request_id": "11111111-1111-1111-1111-111111111111",
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


def test_valid_inventory_v1_payload_parses():
    payload = InventoryPayload.model_validate(VALID_PAYLOAD)
    assert payload.schema_version == "inventory/v1"
    assert payload.sites[0].plugins[0].slug == "akismet"


def test_unsupported_schema_version_rejected():
    bad = {**VALID_PAYLOAD, "schema_version": "inventory/v99"}
    with pytest.raises(ValidationError):
        InventoryPayload.model_validate(bad)


def test_missing_required_field_rejected():
    bad = {**VALID_PAYLOAD}
    del bad["request_id"]
    with pytest.raises(ValidationError):
        InventoryPayload.model_validate(bad)
