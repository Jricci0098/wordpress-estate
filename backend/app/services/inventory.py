from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models import InventorySnapshot, PluginInstallation, Site
from app.schemas.inventory import InventoryPayload


def ingest_inventory(db: Session, agent_id: str, payload: InventoryPayload) -> list[Site]:
    """Persist one inventory payload. Snapshots are append-only.

    Each site's inventory becomes a new InventorySnapshot row plus one
    PluginInstallation row per reported plugin; nothing is ever mutated or
    deleted from prior snapshots. The Site row is upserted for convenience
    (latest known URL/version), but its history lives in the snapshots.
    """
    now = datetime.now(UTC)
    touched_sites: list[Site] = []

    for site_inventory in payload.sites:
        site = db.query(Site).filter(Site.name == site_inventory.site_name).one_or_none()
        if site is None:
            site = Site(
                name=site_inventory.site_name,
                url=site_inventory.site_url,
                host_name=payload.host.hostname,
                wp_version=site_inventory.wp_version,
                first_seen_at=now,
                last_seen_at=now,
            )
            db.add(site)
            db.flush()
        else:
            site.url = site_inventory.site_url
            site.host_name = payload.host.hostname
            site.wp_version = site_inventory.wp_version
            site.last_seen_at = now

        snapshot = InventorySnapshot(
            site_id=site.id,
            agent_id=agent_id,
            request_id=payload.request_id,
            schema_version=payload.schema_version,
            wp_version=site_inventory.wp_version,
            received_at=now,
            raw_payload=site_inventory.model_dump(mode="json"),
        )
        db.add(snapshot)
        db.flush()

        for plugin in site_inventory.plugins:
            db.add(
                PluginInstallation(
                    snapshot_id=snapshot.id,
                    site_id=site.id,
                    slug=plugin.slug,
                    name=plugin.name,
                    version=plugin.version,
                    path=plugin.path,
                    kind=plugin.kind,
                    origin=plugin.origin,
                    status=plugin.status,
                    update_status=plugin.update_status,
                    approval_status=plugin.approval_status,
                )
            )

        touched_sites.append(site)

    db.commit()
    return touched_sites
