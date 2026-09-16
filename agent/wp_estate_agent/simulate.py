"""Synthetic inventory generation for demoing/exercising the API.

Produces a realistic ``inventory/v1`` payload covering five demo WordPress
sites and every plugin origin/kind combination the platform needs to
distinguish: WordPress.org, commercial, custom/in-house, MU plugins,
drop-ins, and completely unknown plugins. This is fabricated demo data,
clearly generated (not a real filesystem scan) — it is only ever used for
local development and smoke testing.
"""

import uuid
from datetime import UTC, datetime

SITE_PORTS = {"wp1": 8181, "wp2": 8182, "wp3": 8183, "wp4": 8184, "wp5": 8185}


def _wordpress_org_plugin(name: str, slug: str, version: str, current: bool) -> dict:
    return {
        "slug": slug,
        "name": name,
        "version": version,
        "path": f"wp-content/plugins/{slug}/{slug}.php",
        "kind": "plugin",
        "origin": "wordpress_org",
        "status": "active",
        "update_status": "current" if current else "behind",
    }


def _commercial_plugin(name: str, slug: str, version: str) -> dict:
    return {
        "slug": slug,
        "name": name,
        "version": version,
        "path": f"wp-content/plugins/{slug}/{slug}.php",
        "kind": "plugin",
        "origin": "commercial",
        "status": "active",
        "update_status": "unknown",
    }


def _custom_plugin(name: str, slug: str, version: str) -> dict:
    return {
        "slug": slug,
        "name": name,
        "version": version,
        "path": f"wp-content/plugins/{slug}/{slug}.php",
        "kind": "plugin",
        "origin": "custom",
        "status": "active",
        "update_status": "unknown",
    }


def _mu_plugin(name: str, slug: str) -> dict:
    return {
        "slug": slug,
        "name": name,
        "version": "1.0",
        "path": f"wp-content/mu-plugins/{slug}.php",
        "kind": "mu-plugin",
        "origin": "unknown",
        "status": "active",
        "update_status": "unknown",
    }


def _dropin(name: str, slug: str) -> dict:
    return {
        "slug": slug,
        "name": name,
        "version": None,
        "path": f"wp-content/{slug}.php",
        "kind": "dropin",
        "origin": "unknown",
        "status": "active",
        "update_status": "unknown",
    }


def _unknown_plugin(name: str, slug: str) -> dict:
    return {
        "slug": slug,
        "name": name,
        "version": "0.1",
        "path": f"wp-content/plugins/{slug}/{slug}.php",
        "kind": "plugin",
        "origin": "unknown",
        "status": "unknown",
        "update_status": "unknown",
    }


def _site_plugins(site_name: str) -> list[dict]:
    common = [
        _wordpress_org_plugin("Akismet Anti-spam", "akismet", "5.3", current=True),
        _wordpress_org_plugin("Yoast SEO", "wordpress-seo", "23.0", current=False),
        _commercial_plugin("Acme SEO Pro", "acme-seo-pro", "2.1.0"),
        _custom_plugin(
            f"{site_name.upper()} Internal Billing Sync", "internal-billing-sync", "0.4.0"
        ),
        _mu_plugin("Force SSL Loader", "force-ssl"),
        _dropin("Object Cache Drop-in", "object-cache"),
        _unknown_plugin("Mystery Plugin", "mystery-plugin"),
    ]
    return common


def generate_simulated_inventory(agent_id: str, hostname: str = "demo-host") -> dict:
    now = datetime.now(UTC)
    sites = []
    for site_name, port in SITE_PORTS.items():
        sites.append(
            {
                "site_name": site_name,
                "site_url": f"http://localhost:{port}",
                "wp_version": "6.6.2",
                "plugins": _site_plugins(site_name),
            }
        )

    return {
        "schema_version": "inventory/v1",
        "agent_id": agent_id,
        "request_id": str(uuid.uuid4()),
        "timestamp": now.isoformat(),
        "host": {"hostname": hostname, "os_info": "simulated"},
        "sites": sites,
    }
