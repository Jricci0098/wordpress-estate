"""wp-estate-agent command-line interface.

This agent is intentionally read-only: it discovers WordPress installations
and plugin metadata on disk and reports it to the estate backend. It has no
shell-execution feature and no update/remediation jobs.
"""

import concurrent.futures
import dataclasses
import json
import os
import uuid
from datetime import UTC, datetime

import click

from wp_estate_agent.client import EstateApiClient
from wp_estate_agent.discover import discover_plugins, find_wordpress_roots
from wp_estate_agent.simulate import generate_simulated_inventory

_API_URL_ENV = "WP_ESTATE_API_URL"
_AGENT_ID_ENV = "WP_ESTATE_AGENT_ID"
_AGENT_SECRET_ENV = "WP_ESTATE_AGENT_SECRET"


def _client_options(func):
    func = click.option(
        "--api-url", default=lambda: os.environ.get(_API_URL_ENV, "http://localhost:8001")
    )(func)
    func = click.option(
        "--agent-id", default=lambda: os.environ.get(_AGENT_ID_ENV, "")
    )(func)
    func = click.option(
        "--agent-secret", default=lambda: os.environ.get(_AGENT_SECRET_ENV, "")
    )(func)
    return func


@click.group()
def cli():
    """Read-only WordPress estate inventory agent."""


@cli.command()
@click.option("--root", "roots", multiple=True, required=True, help="Directory to scan.")
@click.option("--max-depth", default=5, show_default=True)
@click.option("--concurrency", default=4, show_default=True)
def discover(roots: tuple[str, ...], max_depth: int, concurrency: int):
    """Discover WordPress installations and their plugins under ROOTS."""
    wp_roots = find_wordpress_roots(list(roots), max_depth=max_depth)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, concurrency)) as pool:
        plugin_lists = list(pool.map(discover_plugins, wp_roots))

    output = [
        {
            "site_root": str(root),
            "plugins": [dataclasses.asdict(p) for p in plugins],
        }
        for root, plugins in zip(wp_roots, plugin_lists, strict=True)
    ]
    click.echo(json.dumps(output, indent=2))


@cli.command()
@click.option("--root", help="WordPress root directory to scan (ignored if --simulate is set)")
@click.option("--site-name", help="Site name to report (defaults to the root directory name)")
@click.option("--site-url", default="http://localhost", show_default=True)
@click.option("--simulate", is_flag=True, help="Emit fabricated demo inventory instead of scanning")
@click.option("--post", is_flag=True, help="POST the inventory to the backend API")
@_client_options
def inventory(
    root: str | None,
    site_name: str | None,
    site_url: str,
    simulate: bool,
    post: bool,
    api_url: str,
    agent_id: str,
    agent_secret: str,
):
    """Collect (or simulate) inventory and optionally post it to the backend."""
    if simulate:
        payload = generate_simulated_inventory(agent_id=agent_id or "agent-simulated")
    else:
        if not root:
            raise click.UsageError("--root is required unless --simulate is set")
        plugins = discover_plugins(root)
        payload = {
            "schema_version": "inventory/v1",
            "agent_id": agent_id,
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.now(UTC).isoformat(),
            "host": {"hostname": os.environ.get("COMPUTERNAME") or os.uname().nodename},
            "sites": [
                {
                    "site_name": site_name or os.path.basename(os.path.normpath(root)),
                    "site_url": site_url,
                    "wp_version": None,
                    "plugins": [dataclasses.asdict(p) for p in plugins],
                }
            ],
        }

    if post:
        client = EstateApiClient(base_url=api_url, agent_id=agent_id, agent_secret=agent_secret)
        response = client.post_inventory(payload)
        click.echo(json.dumps({"http_status": response.status_code, **response.json()}))
        if response.status_code >= 400:
            raise click.ClickException(
                f"inventory post failed: {response.status_code} {response.text}"
            )
    else:
        click.echo(json.dumps(payload, indent=2))


@cli.command()
@_client_options
def heartbeat(api_url: str, agent_id: str, agent_secret: str):
    """Send a heartbeat to the backend to prove the agent is alive."""
    client = EstateApiClient(base_url=api_url, agent_id=agent_id, agent_secret=agent_secret)
    response = client.heartbeat()
    click.echo(json.dumps({"http_status": response.status_code, **response.json()}))
    if response.status_code >= 400:
        raise click.ClickException(f"heartbeat failed: {response.status_code} {response.text}")


if __name__ == "__main__":
    cli()
