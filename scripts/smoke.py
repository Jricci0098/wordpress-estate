"""End-to-end smoke checks for the local WordPress Estate MVP."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class Check:
    name: str
    url: str
    contains: str | None = None


CHECKS = [
    Check("backend", "http://localhost:8001/health", '"status":"ok"'),
    Check("frontend", "http://localhost:8080/", "WordPress Estate"),
    *[
        Check(
            f"wp{i}",
            f"http://localhost:{8180 + i}/",
            f"WordPress Estate Demo &#8211; wp{i}",
        )
        for i in range(1, 6)
    ],
]


def fetch(url: str) -> str:
    with urllib.request.urlopen(url, timeout=15) as response:
        if response.status != 200:
            raise RuntimeError(f"{url} returned HTTP {response.status}")
        return response.read().decode("utf-8")


def main() -> int:
    failures: list[str] = []
    for check in CHECKS:
        try:
            body = fetch(check.url)
            if check.contains and check.contains not in body:
                raise RuntimeError(f"expected {check.contains!r} in response")
            print(f"PASS {check.name}: {check.url}")
        except Exception as exc:  # smoke runner must aggregate failures
            failures.append(f"{check.name}: {exc}")
            print(f"FAIL {check.name}: {exc}", file=sys.stderr)

    try:
        sites = json.loads(fetch("http://localhost:8001/api/v1/sites?page_size=100"))
        plugins = json.loads(fetch("http://localhost:8001/api/v1/plugins?page_size=100"))
        unknown = json.loads(fetch("http://localhost:8001/api/v1/plugins/unknown?page_size=100"))
        assert sites["total"] == 5, sites
        assert plugins["total"] >= 35, plugins
        assert unknown["total"] >= 5, unknown
        origins = {item["origin"] for item in plugins["items"]}
        kinds = {item["kind"] for item in plugins["items"]}
        assert {"wordpress_org", "commercial", "custom", "unknown"} <= origins
        assert {"plugin", "mu-plugin", "dropin"} <= kinds
        print(
            f"PASS inventory: {sites['total']} sites, {plugins['total']} plugins, "
            f"{unknown['total']} unknown-origin records"
        )
    except Exception as exc:
        failures.append(f"inventory: {exc}")
        print(f"FAIL inventory: {exc}", file=sys.stderr)

    result = subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        failures.append(f"compose config: {result.stderr.strip()}")
        print("FAIL compose config", file=sys.stderr)
    else:
        print("PASS compose config")

    if failures:
        print("\nSmoke failures:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
