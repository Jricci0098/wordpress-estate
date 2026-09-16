# WordPress Estate MVP

A self-hosted, read-only-by-default WordPress estate inventory prototype. It combines a FastAPI/PostgreSQL control plane, a filesystem inventory agent, a React dashboard, and five local WordPress installations for realistic testing.

> This is an MVP, not a production deployment. Automated updates, arbitrary remote shell execution, and MainWP coupling are deliberately excluded.

## What runs

| Component | Local URL | Purpose |
|---|---|---|
| Dashboard | http://localhost:8080 | Sites, plugins, and unknown-plugin views |
| API / OpenAPI | http://localhost:8001/docs | Inventory API and documentation |
| WordPress 1 | http://localhost:8181 | Installed demo site |
| WordPress 2 | http://localhost:8182 | Installed demo site |
| WordPress 3 | http://localhost:8183 | Installed demo site |
| WordPress 4 | http://localhost:8184 | Installed demo site |
| WordPress 5 | http://localhost:8185 | Installed demo site |

Ports 8000 and 8081-8085 are intentionally avoided because other local Collective Cybersecurity test services already use them. The dashboard, API, and WordPress ports are bound to `127.0.0.1` only. PostgreSQL, Redis, and MariaDB are not published to the host.

## Demo credentials

Development only—never reuse these values:

- WordPress username: `admin`
- WordPress password: `AdminDemo123!`
- Agent ID: `agent-demo`
- Agent secret: `demo-agent-secret-change-me`

Change local values in `.env`. That file is ignored by Git; `.env.example` documents all settings.

## Quick start

Prerequisites: Docker Desktop, Docker Compose v2, Python 3.12+, Node.js 20+, and GNU Make through Git Bash.

```bash
cp .env.example .env       # already present in this workspace
make dev                   # build and start the estate plus five WP sites
make demo                  # submit a five-site simulated inventory
make smoke                 # verify HTTP, installed sites, and API inventory
```

The one-shot `wp-bootstrap` container should finish with exit code 0. This is expected; it installs all five sites and seeds harmless demo plugin headers.

Stop without deleting data:

```bash
make down
```

Delete the local databases and WordPress volumes as well:

```bash
docker compose down -v
```

## Development

Create a local environment if needed:

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r backend/requirements-dev.txt -r agent/requirements-dev.txt
cd frontend && npm ci && cd ..
```

Quality gates:

```bash
make test
make lint
make smoke
```

Useful commands:

```bash
make migrate             # run Alembic in the backend container
make seed                # alias for simulated inventory ingestion
make logs                # follow Compose logs
make ps                  # show all service states
```

## Architecture

Agents initiate authenticated HTTPS/API requests to the estate server. The inventory path is:

```text
read-only host agent -> versioned inventory/v1 API -> append-only snapshots
                    -> normalized current views -> React dashboard / CSV
```

The MVP simulation includes WordPress.org, commercial, custom, unknown, MU-plugin, and drop-in records. `installed`, `current`, `approved`, and `secure` remain independent properties. Non-WordPress.org plugins without an update source are `unknown`, never assumed current.

See:

- [Architecture](docs/architecture.md)
- [Security](docs/security.md)
- [Agent](docs/agent.md)
- [Operations](docs/operations.md)
- [Execution evidence](docs/test-evidence.md)

## Current limitations

- The dashboard has no OIDC/RBAC yet and is suitable only for local MVP evaluation.
- Agent bootstrap uses a development seed credential.
- Simulated ingestion proves the five-site estate workflow; filesystem discovery is unit-tested but is not yet deployed as a daemon in each WordPress container.
- Update/vulnerability provider adapters, approval workflows, typed update jobs, MainWP integration, backups, and production TLS are later milestones.
- The worker is a minimal Redis-backed healthy worker scaffold; update automation remains disabled.
