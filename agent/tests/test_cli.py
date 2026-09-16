import json

import httpx
import respx
from click.testing import CliRunner

from wp_estate_agent.cli import cli

STANDARD_HEADER = """<?php
/**
 * Plugin Name: Akismet Anti-spam
 * Plugin URI: https://wordpress.org/plugins/akismet/
 * Version: 5.3
 */
"""


def _make_wp_site(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "wp-config.php").write_text("<?php\n", encoding="utf-8")
    plugins = root / "wp-content" / "plugins" / "akismet"
    plugins.mkdir(parents=True)
    (plugins / "akismet.php").write_text(STANDARD_HEADER, encoding="utf-8")
    return root


def test_discover_command_outputs_json(tmp_path):
    _make_wp_site(tmp_path / "site1")
    runner = CliRunner()

    result = runner.invoke(cli, ["discover", "--root", str(tmp_path), "--max-depth", "3"])

    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert len(data) == 1
    assert data[0]["plugins"][0]["slug"] == "akismet"


def test_inventory_simulate_prints_payload_without_post():
    runner = CliRunner()

    result = runner.invoke(cli, ["inventory", "--simulate"])

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["schema_version"] == "inventory/v1"
    assert len(payload["sites"]) == 5


@respx.mock
def test_inventory_simulate_with_post_calls_api():
    respx.post("http://backend.local/api/v1/inventory").mock(
        return_value=httpx.Response(201, json={"sites_processed": 5})
    )
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "inventory",
            "--simulate",
            "--post",
            "--api-url",
            "http://backend.local",
            "--agent-id",
            "agent-1",
            "--agent-secret",
            "s3cr3t",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "sites_processed" in result.output


@respx.mock
def test_heartbeat_command_success():
    respx.post("http://backend.local/api/v1/heartbeat").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    runner = CliRunner()

    result = runner.invoke(
        cli,
        [
            "heartbeat",
            "--api-url",
            "http://backend.local",
            "--agent-id",
            "agent-1",
            "--agent-secret",
            "s3cr3t",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "ok" in result.output
