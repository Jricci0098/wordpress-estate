# Architecture

## MVP components

- **Backend:** FastAPI, SQLAlchemy 2, Alembic, PostgreSQL.
- **Agent:** read-only Python CLI for discovery, plugin header parsing, heartbeat, and `inventory/v1` submission.
- **Frontend:** React + TypeScript dashboard.
- **Worker:** minimal Redis-connected worker scaffold; no update execution.
- **Demo estate:** one MariaDB server, five isolated WordPress containers/volumes, and one WP-CLI bootstrap job.

## Trust and data flow

```text
Host filesystem
  -> read-only agent
  -> per-agent authenticated POST /api/v1/inventory
  -> schema validation + replay check
  -> append-only inventory snapshots in PostgreSQL
  -> current paginated API views
  -> browser dashboard / CSV export
```

The agent initiates communication. The server does not require inbound SSH to managed hosts. Agent execution and arbitrary shell endpoints do not exist in this milestone.

## Data semantics

A plugin directory or slug is observed inventory, not a guaranteed canonical identity. The MVP stores observations and origins while preserving snapshot history. Later milestones add canonical product identity and manual resolution.

These dimensions are intentionally independent:

- installed
- current/update status
- security status
- approval status
- support/lifecycle status
- licensing status

Commercial, custom, and unknown plugins without a configured provider remain update status `unknown`.

## Networking

Only the dashboard, API, and five local WordPress sites publish ports. Database and queue services stay on the Compose network. WordPress ports bind only to loopback.
