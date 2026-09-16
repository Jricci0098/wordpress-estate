from wp_estate_agent.discover import discover_plugins, find_wordpress_roots

STANDARD_HEADER = """<?php
/**
 * Plugin Name: Akismet Anti-spam
 * Plugin URI: https://wordpress.org/plugins/akismet/
 * Version: 5.3
 * Author: Automattic
 */
"""

COMMERCIAL_HEADER = """<?php
/**
 * Plugin Name: Acme SEO Pro
 * Plugin URI: https://acme.example.com/seo-pro
 * Version: 2.1.0
 * Author: Acme Software
 */
"""

CUSTOM_HEADER = """<?php
/**
 * Plugin Name: Internal Billing Sync
 * Version: 0.4.0
 */
"""

MU_HEADER = """<?php
/**
 * Plugin Name: Force SSL Loader
 * Version: 1.0
 */
"""


def _make_wp_site(root):
    root.mkdir(parents=True, exist_ok=True)
    (root / "wp-config.php").write_text("<?php // config\n", encoding="utf-8")

    plugins = root / "wp-content" / "plugins"
    (plugins / "akismet").mkdir(parents=True)
    (plugins / "akismet" / "akismet.php").write_text(STANDARD_HEADER, encoding="utf-8")

    (plugins / "acme-seo-pro").mkdir(parents=True)
    (plugins / "acme-seo-pro" / "acme-seo-pro.php").write_text(
        COMMERCIAL_HEADER, encoding="utf-8"
    )

    (plugins / "internal-billing-sync").mkdir(parents=True)
    (plugins / "internal-billing-sync" / "internal-billing-sync.php").write_text(
        CUSTOM_HEADER, encoding="utf-8"
    )

    mu_plugins = root / "wp-content" / "mu-plugins"
    mu_plugins.mkdir(parents=True)
    (mu_plugins / "force-ssl.php").write_text(MU_HEADER, encoding="utf-8")

    (root / "wp-content" / "object-cache.php").write_text(
        "<?php\n// drop-in, no plugin header\n", encoding="utf-8"
    )
    return root


def test_find_wordpress_roots_locates_wp_config(tmp_path):
    site_root = _make_wp_site(tmp_path / "site1")
    (tmp_path / "not-a-site").mkdir()

    roots = find_wordpress_roots([tmp_path], max_depth=3)

    assert site_root.resolve() in [r.resolve() for r in roots]
    assert len(roots) == 1


def test_discover_plugins_classifies_all_kinds(tmp_path):
    site_root = _make_wp_site(tmp_path / "site1")

    plugins = discover_plugins(site_root)
    by_slug = {p.slug: p for p in plugins}

    assert by_slug["akismet"].kind == "plugin"
    assert by_slug["akismet"].origin == "wordpress_org"
    assert by_slug["akismet"].version == "5.3"

    assert by_slug["acme-seo-pro"].origin == "commercial"
    assert by_slug["internal-billing-sync"].origin == "custom"

    assert by_slug["force-ssl"].kind == "mu-plugin"

    assert by_slug["object-cache"].kind == "dropin"
    assert by_slug["object-cache"].origin == "unknown"

    assert len(plugins) == 5


def test_find_wordpress_roots_respects_max_depth(tmp_path):
    deep_root = tmp_path / "a" / "b" / "c" / "d" / "site"
    _make_wp_site(deep_root)

    roots = find_wordpress_roots([tmp_path], max_depth=1)
    assert roots == []
