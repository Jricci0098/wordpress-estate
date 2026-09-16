# WordPress Estate MVP implementation brief

## Goal
Build and actually run a local MVP of the WordPress Estate Management Platform described by the user. This iteration intentionally covers the first useful vertical slice, not all 50 requirements.

## Collaboration and safety
- Claude Code is the implementer. Cursor will independently review the final uncommitted diff in read-only Ask mode.
- Do not commit, push, open a PR, or modify anything outside this repository.
- Keep the estate agent read-only. No generic shell execution and no update jobs.
- Do not put secrets in source; use local-only development defaults and `.env.example`.
- Use strict RED-GREEN-REFACTOR for application behavior: write a focused failing test, run it and confirm the expected failure, implement minimally, rerun it, then continue. Record the RED and GREEN commands/results in `docs/test-evidence.md`.

## MVP scope
Create a maintainable monorepo with:

1. **Backend**: Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL, Pydantic v2.
   - Models sufficient for hosts, sites, inventory snapshots, plugin products, and plugin installations.
   - Versioned inventory schema (`inventory/v1`).
   - Per-agent authentication with unique agent ID and secret; store only a secret hash. For local bootstrap, credentials may come from environment/seed data.
   - Replay resistance using request ID + timestamp freshness and a uniqueness constraint for request IDs.
   - Endpoints: health, heartbeat, inventory ingestion, paginated sites, paginated plugins, unknown plugins, and CSV export.
   - Historical snapshots are append-only. Duplicate request IDs are rejected.
   - Update/security/approval states remain distinct. Commercial/custom plugins with no source are `unknown`, never `current`.

2. **Agent**: lightweight Python CLI, not a WordPress plugin.
   - `discover`, `inventory`, `heartbeat`, and `inventory --simulate`.
   - Configurable roots, `wp-config.php`, max depth, concurrency.
   - Filesystem discovery and plugin-header parsing, including ordinary plugins and MU plugins. Represent drop-ins where found.
   - Execution/jobs disabled by default. No arbitrary shell feature.
   - Simulation mode emits realistic inventory with WordPress.org, commercial, custom, MU, drop-in, and unknown examples and can post it to the API.

3. **Frontend**: React + TypeScript (Vite is fine) with a simple usable dashboard.
   - Overview counts, Sites table, Plugins table, Unknown Plugins view.
   - Fetch data from the API and show loading/error states.
   - Avoid pretending that installed/current/approved/secure are the same.

4. **Containerized local environment**:
   - `docker compose up -d --build` must run PostgreSQL, Redis, backend, worker (a minimal real queue worker or clearly documented placeholder healthful worker), frontend, one shared MariaDB service, and **five distinct running WordPress containers** named/sites `wp1` through `wp5`.
   - Expose the five WordPress sites on localhost ports 8081-8085.
   - Automatically bootstrap all five as installed WordPress sites with deterministic local demo credentials documented in README (development only), not merely the installer screen.
   - Seed the sites with a varied set of harmless demo plugin files/headers where practical so inventory behavior can be exercised. Do not download commercial plugins.
   - Provide health checks and avoid exposing PostgreSQL/Redis to host unless needed for development; they must not be externally published by default.
   - Provide a reliable script/Make target that posts simulated inventory covering all five sites to the backend.

5. **Developer UX/docs**:
   - `Makefile` targets: `dev`, `down`, `test`, `lint`, `migrate`, `seed`, `demo`, `smoke` (Windows Git Bash compatible).
   - Root README with exact commands, URLs, credentials, architecture, limitations, and cleanup.
   - Docs for architecture, security, agent, and MVP operations.
   - Structured JSON logging where practical.

## Required tests
At minimum test:
- inventory schema validation and unsupported schema rejection;
- valid agent auth, invalid secret, stale timestamp, duplicate/replayed request ID;
- append-only snapshots and idempotent/rejected duplicate behavior;
- pagination bounds;
- unknown/commercial/custom status handling;
- filesystem WordPress discovery;
- plugin header parsing for standard, commercial/custom, MU plugin, and drop-in examples;
- agent simulation payload;
- frontend production build;
- Compose config validity.

Use SQLite only for fast unit tests if abstractions remain PostgreSQL-compatible; include at least one real PostgreSQL integration/smoke path through Compose.

## Verification before stopping
Do not stop at scaffolding. Run and report real results for:
1. backend/agent tests and lint;
2. frontend tests/lint/build;
3. `docker compose config`;
4. `docker compose up -d --build`;
5. wait for health, then prove HTTP 200 from backend, frontend, and each of ports 8081-8085;
6. prove each WordPress site is installed (homepage/site title or WP API response, not installer screen);
7. post inventory for five sites and verify the API lists them and includes unknown/custom/commercial/MU/drop-in coverage;
8. capture `docker compose ps` in `docs/test-evidence.md`.

If a dependency or environment problem blocks verification, diagnose it and make the smallest justified correction. Do not fabricate output.
