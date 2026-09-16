"""WordPress plugin header parsing and origin classification.

Mirrors the subset of the standard WordPress plugin header docblock format
(https://developer.wordpress.org/plugins/plugin-basics/header-requirements/)
that we need, plus an optional non-standard ``Origin`` field that lets a
plugin explicitly self-declare its origin when the heuristic would guess
wrong.
"""

import re
from pathlib import Path
from typing import Literal

PluginOrigin = Literal["wordpress_org", "commercial", "custom", "unknown"]

_HEADER_FIELDS = {
    "name": re.compile(r"^\s*\*?\s*Plugin Name:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "version": re.compile(r"^\s*\*?\s*Version:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "plugin_uri": re.compile(r"^\s*\*?\s*Plugin URI:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "author": re.compile(r"^\s*\*?\s*Author:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "author_uri": re.compile(r"^\s*\*?\s*Author URI:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "text_domain": re.compile(r"^\s*\*?\s*Text Domain:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "license": re.compile(r"^\s*\*?\s*License:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
    "origin": re.compile(r"^\s*\*?\s*Origin:\s*(.+)$", re.MULTILINE | re.IGNORECASE),
}

_READ_LIMIT = 8192  # WordPress itself only reads the first 8 KiB for headers


def parse_plugin_header(path: Path) -> dict | None:
    """Parse a plugin/MU-plugin header docblock from ``path``.

    Returns ``None`` if no ``Plugin Name`` field is found (e.g. drop-ins,
    or arbitrary PHP files with no header at all).
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")[:_READ_LIMIT]
    except OSError:
        return None

    name_match = _HEADER_FIELDS["name"].search(text)
    if not name_match:
        return None

    header: dict[str, str | None] = {"name": name_match.group(1).strip()}
    for field, pattern in _HEADER_FIELDS.items():
        if field == "name":
            continue
        match = pattern.search(text)
        header[field] = match.group(1).strip() if match else None
    return header


def classify_origin(header: dict | None) -> PluginOrigin:
    """Classify a parsed header's plugin origin.

    An explicit ``Origin`` header field always wins. Otherwise: a
    ``wordpress.org/plugins/`` URI means the plugin is distributed on
    WordPress.org; any other URI/author info means a commercial vendor;
    a bare header with a name but no URI/author is treated as in-house
    "custom" code; no header at all is "unknown" (we cannot identify it).
    """
    if header is None:
        return "unknown"

    explicit = (header.get("origin") or "").strip().lower()
    if explicit in ("wordpress_org", "commercial", "custom", "unknown"):
        return explicit  # type: ignore[return-value]

    plugin_uri = header.get("plugin_uri") or ""
    author_uri = header.get("author_uri") or ""
    if "wordpress.org/plugins/" in plugin_uri or "wordpress.org/plugins/" in author_uri:
        return "wordpress_org"

    if plugin_uri or author_uri:
        return "commercial"

    return "custom"
