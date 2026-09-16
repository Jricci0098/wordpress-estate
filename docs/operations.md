# MVP Operations

## Start and verify

```bash
make dev
make demo
make smoke
docker compose ps -a
```

Expected state: backend, frontend, PostgreSQL, Redis, MariaDB, worker, and `wp1` through `wp5` are running; `wp-bootstrap` is exited with code 0.

## URLs

- Dashboard: http://localhost:8080
- API docs: http://localhost:8001/docs
- WordPress: http://localhost:8181 through http://localhost:8185

## Logs and diagnostics

```bash
docker compose logs --tail=200 backend
docker compose logs --tail=200 wp-bootstrap
docker compose logs --tail=200 mariadb
make ps
```

If local ports conflict, change `BACKEND_PORT`, `FRONTEND_PORT`, `WP1_PORT` through `WP5_PORT`, and matching `WP_PORT_BASE`/`VITE_API_URL` values in `.env`. Rebuild the frontend whenever `VITE_API_URL` changes.

## Restart

```bash
make down
make dev
```

Persistent volumes retain the databases and WordPress files. The bootstrap job is idempotent: installed sites are skipped, and demo plugin files are refreshed.

## Reset all MVP data

```bash
docker compose down -v
make dev
make demo
```

This is destructive and removes only volumes owned by this Compose project.

## Database migrations

```bash
make migrate
```

The backend entrypoint also applies migrations before starting Uvicorn.

## Export

```bash
curl -fsS http://localhost:8001/api/v1/export/plugins.csv -o plugins.csv
```
