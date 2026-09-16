#!/bin/sh
# Bootstraps all five demo WordPress sites: waits for each site's
# wp-config.php (written by the official wordpress image on first boot),
# runs a real `wp core install` so the sites are actually installed (not
# left on the installer screen), then seeds a small set of harmless demo
# plugin files covering wordpress.org, commercial, custom, and MU-plugin
# origins so agent inventory discovery has something varied to report on.
#
# This script never downloads anything from the network: the wordpress.org
# examples are Akismet/Hello Dolly, which ship bundled with WordPress core.
set -e

ADMIN_USER="${WP_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${WP_ADMIN_PASSWORD:-AdminDemo123!}"
ADMIN_EMAIL="${WP_ADMIN_EMAIL:-admin@example.local}"
PORT_BASE="${WP_PORT_BASE:-8180}"

for i in 1 2 3 4 5; do
  SITE="wp$i"
  SITE_PATH="/var/www/$SITE"
  PORT=$((PORT_BASE + i))
  URL="http://localhost:$PORT"
  # The official wp-config.php resolves database settings from environment
  # variables each time it runs. Select the matching database for this volume.
  export WORDPRESS_DB_NAME="$SITE"

  echo "=== Bootstrapping $SITE at $URL ==="

  attempt=0
  until [ -f "$SITE_PATH/wp-config.php" ]; do
    attempt=$((attempt + 1))
    if [ "$attempt" -gt 30 ]; then
      echo "ERROR: $SITE_PATH/wp-config.php never appeared" >&2
      exit 1
    fi
    echo "waiting for $SITE_PATH/wp-config.php (attempt $attempt/30)..."
    sleep 2
  done

  if wp core is-installed --path="$SITE_PATH" --allow-root >/dev/null 2>&1; then
    echo "$SITE already installed, skipping core install"
  else
    wp core install \
      --path="$SITE_PATH" \
      --url="$URL" \
      --title="WordPress Estate Demo - $SITE" \
      --admin_user="$ADMIN_USER" \
      --admin_password="$ADMIN_PASSWORD" \
      --admin_email="$ADMIN_EMAIL" \
      --skip-email \
      --allow-root
  fi

  mkdir -p "$SITE_PATH/wp-content/plugins/acme-seo-pro"
  cp /demo-plugins/acme-seo-pro.php "$SITE_PATH/wp-content/plugins/acme-seo-pro/acme-seo-pro.php"

  mkdir -p "$SITE_PATH/wp-content/plugins/internal-billing-sync"
  cp /demo-plugins/internal-billing-sync.php \
    "$SITE_PATH/wp-content/plugins/internal-billing-sync/internal-billing-sync.php"

  mkdir -p "$SITE_PATH/wp-content/plugins/mystery-plugin"
  cp /demo-plugins/mystery-plugin.php "$SITE_PATH/wp-content/plugins/mystery-plugin/mystery-plugin.php"

  mkdir -p "$SITE_PATH/wp-content/mu-plugins"
  cp /demo-plugins/force-ssl.php "$SITE_PATH/wp-content/mu-plugins/force-ssl.php"

  # Akismet + Hello Dolly ship bundled with WordPress core (no network needed)
  # and are real wordpress.org-origin plugins, useful for realistic inventory.
  wp plugin activate akismet --path="$SITE_PATH" --allow-root || true
  wp plugin activate hello --path="$SITE_PATH" --allow-root || true
  wp plugin activate acme-seo-pro --path="$SITE_PATH" --allow-root || true

  echo "=== $SITE bootstrap complete ==="
done

echo "All five sites bootstrapped."
