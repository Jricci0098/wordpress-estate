import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import InventorySnapshot, PluginInstallation, Site

router = APIRouter(prefix="/api/v1")

CSV_FIELDS = [
    "site_name",
    "slug",
    "name",
    "version",
    "kind",
    "origin",
    "status",
    "update_status",
    "approval_status",
    "path",
]


def _latest_snapshot_ids(db: Session):
    from sqlalchemy import func

    ranked = (
        select(
            InventorySnapshot.id,
            func.row_number()
            .over(
                partition_by=InventorySnapshot.site_id,
                order_by=InventorySnapshot.received_at.desc(),
            )
            .label("rn"),
        )
    ).subquery()
    return select(ranked.c.id).where(ranked.c.rn == 1)


def _latest_plugins_query(db: Session, unknown_only: bool = False):
    latest_ids = _latest_snapshot_ids(db)
    q = (
        db.query(PluginInstallation, Site.name.label("site_name"))
        .join(Site, Site.id == PluginInstallation.site_id)
        .filter(PluginInstallation.snapshot_id.in_(latest_ids))
    )
    if unknown_only:
        q = q.filter(PluginInstallation.origin == "unknown")
    return q.order_by(Site.name, PluginInstallation.slug)


def _plugin_row_to_dict(installation: PluginInstallation, site_name: str) -> dict:
    return {
        "id": installation.id,
        "site_name": site_name,
        "slug": installation.slug,
        "name": installation.name,
        "version": installation.version,
        "path": installation.path,
        "kind": installation.kind,
        "origin": installation.origin,
        "status": installation.status,
        "update_status": installation.update_status,
        "approval_status": installation.approval_status,
    }


@router.get("/sites")
def list_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    total = db.query(Site).count()
    sites = (
        db.query(Site).order_by(Site.name).offset((page - 1) * page_size).limit(page_size).all()
    )
    items = []
    for site in sites:
        snapshot_count = (
            db.query(InventorySnapshot).filter(InventorySnapshot.site_id == site.id).count()
        )
        items.append(
            {
                "id": site.id,
                "name": site.name,
                "url": site.url,
                "wp_version": site.wp_version,
                "host_name": site.host_name,
                "snapshot_count": snapshot_count,
                "last_seen_at": site.last_seen_at.isoformat(),
            }
        )
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/plugins")
def list_plugins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    q = _latest_plugins_query(db)
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    items = [_plugin_row_to_dict(installation, site_name) for installation, site_name in rows]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.get("/plugins/unknown")
def list_unknown_plugins(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    q = _latest_plugins_query(db, unknown_only=True)
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    items = [_plugin_row_to_dict(installation, site_name) for installation, site_name in rows]
    return {"total": total, "page": page, "page_size": page_size, "items": items}


_FORMULA_PREFIXES = ("=", "+", "-", "@")


def _csv_safe(value: str) -> str:
    """Neutralize CSV formula injection for values opened in spreadsheet apps.

    A cell beginning with =, +, -, or @ can be interpreted as a formula by
    Excel/Sheets/LibreOffice, letting attacker-controlled inventory data
    (e.g. a plugin name or path) execute when an operator opens the export.
    Prefixing with a single quote forces text interpretation.
    """
    if value and value.startswith(_FORMULA_PREFIXES):
        return f"'{value}"
    return value


@router.get("/export/plugins.csv")
def export_plugins_csv(db: Session = Depends(get_db)) -> PlainTextResponse:
    rows = _latest_plugins_query(db).all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(CSV_FIELDS)
    for installation, site_name in rows:
        writer.writerow(
            [
                _csv_safe(site_name),
                _csv_safe(installation.slug),
                _csv_safe(installation.name),
                _csv_safe(installation.version or ""),
                installation.kind,
                installation.origin,
                installation.status,
                installation.update_status,
                installation.approval_status,
                _csv_safe(installation.path),
            ]
        )
    return PlainTextResponse(content=buf.getvalue(), media_type="text/csv")
