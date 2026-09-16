"""Read-only filesystem discovery of WordPress installations and plugins.

This module only ever reads files; it never executes anything found on
disk and never makes network calls.
"""

import os
from pathlib import Path

from wp_estate_agent.models import DiscoveredPlugin
from wp_estate_agent.parser import classify_origin, parse_plugin_header

DROPIN_FILENAMES = {
    "advanced-cache.php",
    "db.php",
    "object-cache.php",
    "install.php",
    "maintenance.php",
    "sunrise.php",
    "blog-deleted.php",
    "blog-inactive.php",
    "blog-suspended.php",
    "fatal-error-handler.php",
    "php-error.php",
}


def find_wordpress_roots(
    roots: list[Path], max_depth: int = 5, wp_config_filename: str = "wp-config.php"
) -> list[Path]:
    """Find directories under ``roots`` that contain a wp-config file.

    Descends at most ``max_depth`` directory levels below each root.
    """
    found: list[Path] = []
    for base in roots:
        base = Path(base)
        base_depth = len(base.resolve().parts)
        for dirpath, dirnames, _filenames in os.walk(base):
            current = Path(dirpath)
            depth = len(current.resolve().parts) - base_depth
            if depth > max_depth:
                dirnames[:] = []
                continue
            if (current / wp_config_filename).is_file():
                found.append(current)
                dirnames[:] = []  # a WordPress root's own subtree isn't searched further
    return found


def discover_plugins(wp_root: Path) -> list[DiscoveredPlugin]:
    """Discover ordinary plugins, MU plugins, and drop-ins under ``wp_root``."""
    wp_root = Path(wp_root)
    wp_content = wp_root / "wp-content"
    results: list[DiscoveredPlugin] = []

    plugins_dir = wp_content / "plugins"
    if plugins_dir.is_dir():
        for entry in sorted(plugins_dir.iterdir()):
            plugin = None
            if entry.is_dir():
                plugin = _discover_plugin_in_dir(entry, wp_root)
            elif entry.suffix == ".php":
                plugin = _discover_single_file(entry, wp_root, kind="plugin")
            if plugin:
                results.append(plugin)

    mu_plugins_dir = wp_content / "mu-plugins"
    if mu_plugins_dir.is_dir():
        for entry in sorted(mu_plugins_dir.glob("*.php")):
            plugin = _discover_single_file(entry, wp_root, kind="mu-plugin")
            if plugin:
                results.append(plugin)

    if wp_content.is_dir():
        for filename in sorted(DROPIN_FILENAMES):
            candidate = wp_content / filename
            if candidate.is_file():
                results.append(_discover_dropin(candidate, wp_root))

    return results


def _discover_plugin_in_dir(plugin_dir: Path, wp_root: Path) -> DiscoveredPlugin | None:
    main_candidate = plugin_dir / f"{plugin_dir.name}.php"
    candidates = (
        [main_candidate] if main_candidate.is_file() else sorted(plugin_dir.glob("*.php"))
    )
    for candidate in candidates:
        header = parse_plugin_header(candidate)
        if header:
            return DiscoveredPlugin(
                slug=plugin_dir.name,
                name=header["name"],
                version=header.get("version"),
                path=str(candidate.relative_to(wp_root)).replace("\\", "/"),
                kind="plugin",
                origin=classify_origin(header),
            )
    return None


def _discover_single_file(file_path: Path, wp_root: Path, kind) -> DiscoveredPlugin | None:
    header = parse_plugin_header(file_path)
    if header is None:
        return None
    return DiscoveredPlugin(
        slug=file_path.stem,
        name=header["name"],
        version=header.get("version"),
        path=str(file_path.relative_to(wp_root)).replace("\\", "/"),
        kind=kind,
        origin=classify_origin(header),
    )


def _discover_dropin(file_path: Path, wp_root: Path) -> DiscoveredPlugin:
    header = parse_plugin_header(file_path)
    return DiscoveredPlugin(
        slug=file_path.stem,
        name=header["name"] if header else file_path.name,
        version=header.get("version") if header else None,
        path=str(file_path.relative_to(wp_root)).replace("\\", "/"),
        kind="dropin",
        origin="unknown",
    )
