import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(primary_key=True)
    secret_hash: Mapped[str] = mapped_column()
    description: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)
    last_seen_at: Mapped[datetime | None] = mapped_column(default=None)

    request_logs: Mapped[list["AgentRequestLog"]] = relationship(back_populates="agent")


class AgentRequestLog(Base):
    """Replay-resistance ledger: (agent_id, request_id) must be unique."""

    __tablename__ = "agent_request_log"
    __table_args__ = (UniqueConstraint("agent_id", "request_id", name="uq_agent_request"),)

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"))
    request_id: Mapped[str] = mapped_column()
    endpoint: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=_utcnow)

    agent: Mapped["Agent"] = relationship(back_populates="request_logs")


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(unique=True)
    url: Mapped[str] = mapped_column()
    host_name: Mapped[str | None] = mapped_column(default=None)
    wp_version: Mapped[str | None] = mapped_column(default=None)
    first_seen_at: Mapped[datetime] = mapped_column(default=_utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(default=_utcnow)

    snapshots: Mapped[list["InventorySnapshot"]] = relationship(back_populates="site")


class InventorySnapshot(Base):
    """Append-only record of a single inventory ingestion for one site."""

    __tablename__ = "inventory_snapshots"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"))
    agent_id: Mapped[str] = mapped_column(ForeignKey("agents.id"))
    request_id: Mapped[str] = mapped_column()
    schema_version: Mapped[str] = mapped_column()
    wp_version: Mapped[str | None] = mapped_column(default=None)
    received_at: Mapped[datetime] = mapped_column(default=_utcnow)
    raw_payload: Mapped[dict] = mapped_column(JSON)

    site: Mapped["Site"] = relationship(back_populates="snapshots")
    installations: Mapped[list["PluginInstallation"]] = relationship(back_populates="snapshot")


class PluginInstallation(Base):
    """A plugin as observed within one inventory snapshot (append-only)."""

    __tablename__ = "plugin_installations"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    snapshot_id: Mapped[str] = mapped_column(ForeignKey("inventory_snapshots.id"))
    site_id: Mapped[str] = mapped_column(ForeignKey("sites.id"))
    slug: Mapped[str] = mapped_column()
    name: Mapped[str] = mapped_column()
    version: Mapped[str | None] = mapped_column(default=None)
    path: Mapped[str] = mapped_column()
    kind: Mapped[str] = mapped_column()
    origin: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column()
    update_status: Mapped[str] = mapped_column()
    approval_status: Mapped[str] = mapped_column(default="unknown")

    snapshot: Mapped["InventorySnapshot"] = relationship(back_populates="installations")
