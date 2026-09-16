from wp_estate_agent.parser import classify_origin, parse_plugin_header

STANDARD_HEADER = """<?php
/**
 * Plugin Name: Akismet Anti-spam
 * Plugin URI: https://wordpress.org/plugins/akismet/
 * Description: Used by millions.
 * Version: 5.3
 * Author: Automattic
 * Author URI: https://automattic.com/wordpress-plugins/
 * Text Domain: akismet
 */
"""

COMMERCIAL_HEADER = """<?php
/**
 * Plugin Name: Acme SEO Pro
 * Plugin URI: https://acme.example.com/seo-pro
 * Description: Paid SEO toolkit.
 * Version: 2.1.0
 * Author: Acme Software
 * Author URI: https://acme.example.com
 */
"""

CUSTOM_HEADER = """<?php
/**
 * Plugin Name: Internal Billing Sync
 * Description: In-house billing sync job.
 * Version: 0.4.0
 */
"""

EXPLICIT_ORIGIN_HEADER = """<?php
/**
 * Plugin Name: Weird But Labeled
 * Origin: custom
 * Author URI: https://wordpress.org/plugins/weird/
 * Version: 1.0
 */
"""


def _write(tmp_path, name: str, content: str):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def test_parse_standard_plugin_header(tmp_path):
    path = _write(tmp_path, "akismet.php", STANDARD_HEADER)
    header = parse_plugin_header(path)
    assert header["name"] == "Akismet Anti-spam"
    assert header["version"] == "5.3"
    assert header["plugin_uri"] == "https://wordpress.org/plugins/akismet/"
    assert header["author"] == "Automattic"


def test_parse_header_returns_none_when_no_header_present(tmp_path):
    path = _write(tmp_path, "object-cache.php", "<?php\n// no plugin header here\n")
    header = parse_plugin_header(path)
    assert header is None


def test_classify_origin_wordpress_org(tmp_path):
    path = _write(tmp_path, "akismet.php", STANDARD_HEADER)
    header = parse_plugin_header(path)
    assert classify_origin(header) == "wordpress_org"


def test_classify_origin_commercial(tmp_path):
    path = _write(tmp_path, "acme-seo.php", COMMERCIAL_HEADER)
    header = parse_plugin_header(path)
    assert classify_origin(header) == "commercial"


def test_classify_origin_custom(tmp_path):
    path = _write(tmp_path, "internal-billing.php", CUSTOM_HEADER)
    header = parse_plugin_header(path)
    assert classify_origin(header) == "custom"


def test_classify_origin_explicit_override_wins(tmp_path):
    path = _write(tmp_path, "weird.php", EXPLICIT_ORIGIN_HEADER)
    header = parse_plugin_header(path)
    assert classify_origin(header) == "custom"


def test_classify_origin_unknown_when_no_header():
    assert classify_origin(None) == "unknown"
