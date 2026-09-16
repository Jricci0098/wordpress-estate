# Test Evidence Log (RED → GREEN)

This log records real command output captured while building the MVP under
strict TDD. Each entry shows the failing (RED) run before the code existed,
then the passing (GREEN) run after the minimal implementation was added.

All backend/agent commands were run with:

```
source .venv/Scripts/activate && unset PYTHONPATH
```

(`PYTHONPATH` is unset because this Windows machine has a global env var
pointing at an unrelated tool's site-packages, which otherwise leaks
incompatible package versions into any venv.)

---

## 1. Inventory schema validation (`inventory/v1`)

**RED** — `python -m pytest tests/unit/test_inventory_schema.py -v` (before `app/schemas/inventory.py` existed):

```
ModuleNotFoundError: No module named 'app.schemas'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.44s
```

**GREEN** — same command after implementing `app/schemas/inventory.py`:

```
tests/unit/test_inventory_schema.py::test_valid_inventory_v1_payload_parses PASSED [ 33%]
tests/unit/test_inventory_schema.py::test_unsupported_schema_version_rejected PASSED [ 66%]
tests/unit/test_inventory_schema.py::test_missing_required_field_rejected PASSED [100%]
3 passed in 1.14s
```

---

## 2. Agent authentication + replay resistance

**RED** — `python -m pytest tests/unit/test_auth.py -v` (before `app/auth.py` existed):

```
ModuleNotFoundError: No module named 'app.auth'
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 1.15s
```

**GREEN** — same command after implementing `app/auth.py` (PBKDF2-HMAC secret hashing,
timestamp freshness window, unique `(agent_id, request_id)` replay ledger):

```
tests/unit/test_auth.py::test_valid_agent_auth_succeeds PASSED           [ 20%]
tests/unit/test_auth.py::test_invalid_secret_rejected PASSED             [ 40%]
tests/unit/test_auth.py::test_unknown_agent_rejected PASSED              [ 60%]
tests/unit/test_auth.py::test_stale_timestamp_rejected PASSED            [ 80%]
tests/unit/test_auth.py::test_duplicate_request_id_rejected PASSED       [100%]
5 passed in 2.28s
```

---

## 3. Inventory ingestion, append-only snapshots, pagination, status handling, unknown plugins, CSV export

**RED** — `python -m pytest tests/ -v` (before `app/main.py`, routers, or `app/services/inventory.py` existed):

```
ImportError while loading conftest 'tests/integration/conftest.py'.
tests\integration\conftest.py:10: in <module>
    from app.main import app
E   ModuleNotFoundError: No module named 'app.main'
```

**Intermediate** (real bug found and fixed during GREEN, not fabricated):
first pass after implementing `app/main.py` + routers failed with
`sqlalchemy.exc.OperationalError: no such table: agents` — the SQLite
`:memory:` test fixtures were opening a *new, separate* in-memory database on
every connection instead of reusing one. Fixed by adding `poolclass=StaticPool`
in `tests/conftest.py` and `tests/integration/conftest.py`.

A second bug surfaced after that fix: `test_varied_plugin_sources_persist_distinctly`
got a spurious 422. Root cause: `test_status_and_unknown.py`'s `_payload()` helper
passed the module-level `VARIED_PLUGINS` list by reference, so an earlier test's
in-place mutation (`update_status = "current"`) permanently corrupted the shared
fixture data for later tests. Fixed with `copy.deepcopy(VARIED_PLUGINS)`.

**GREEN** — `python -m pytest tests/ -v` after implementing `app/main.py`,
`app/routers/{health,agent,catalog}.py`, `app/services/inventory.py`, and fixing
the two bugs above:

```
tests/integration/test_csv_export.py::test_csv_export_contains_plugin_rows PASSED
tests/integration/test_health_and_heartbeat.py::test_health_check PASSED
tests/integration/test_health_and_heartbeat.py::test_heartbeat_requires_valid_auth PASSED
tests/integration/test_health_and_heartbeat.py::test_heartbeat_rejects_replay PASSED
tests/integration/test_inventory_ingestion.py::test_ingest_creates_site_and_snapshot PASSED
tests/integration/test_inventory_ingestion.py::test_snapshots_are_append_only PASSED
tests/integration/test_inventory_ingestion.py::test_duplicate_request_id_is_rejected PASSED
tests/integration/test_inventory_ingestion.py::test_unsupported_schema_version_rejected PASSED
tests/integration/test_inventory_ingestion.py::test_invalid_secret_rejected PASSED
tests/integration/test_pagination.py::test_sites_pagination_bounds PASSED
tests/integration/test_pagination.py::test_sites_pagination_rejects_invalid_params PASSED
tests/integration/test_pagination.py::test_plugins_pagination_bounds PASSED
tests/integration/test_status_and_unknown.py::test_commercial_and_custom_reject_current_status PASSED
tests/integration/test_status_and_unknown.py::test_varied_plugin_sources_persist_distinctly PASSED
tests/integration/test_status_and_unknown.py::test_unknown_plugins_endpoint_lists_only_unknown_origin PASSED
tests/unit/test_auth.py (5) PASSED
tests/unit/test_inventory_schema.py (3) PASSED
23 passed, 1 warning in 10.63s
```

**Lint** — `ruff check app tests` → `All checks passed!` (after `--fix` for import-sort /
`datetime.UTC` style nits).

---

## 4. Alembic migration (initial schema)

Autogenerated from `app/models.py` against a throwaway SQLite DB, then verified with a
real upgrade/downgrade round trip:

```
$ DATABASE_URL="sqlite:////tmp/alembic_gen.db" python -m alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade  -> 15002473b31f, initial schema
$ DATABASE_URL="sqlite:////tmp/alembic_gen.db" python -m alembic downgrade base
INFO  [alembic.runtime.migration] Running downgrade 15002473b31f -> , initial schema
```

(Re-run for real against Postgres via `make migrate` once Compose is up — see §8.)

---

## 5. Agent: plugin header parsing + origin classification

**RED** — `python -m pytest tests/test_parser.py -v` (before `wp_estate_agent/parser.py` existed):

```
ModuleNotFoundError: No module named 'wp_estate_agent.parser'
1 error in 0.39s
```

**GREEN** — after implementing `parser.py` (regex-based WordPress header block parsing +
`classify_origin` heuristic: explicit `Origin:` header wins; `wordpress.org/plugins/` URI →
`wordpress_org`; any other URI/author → `commercial`; name-only header → `custom`; no header → `unknown`):

```
tests/test_parser.py::test_parse_standard_plugin_header PASSED
tests/test_parser.py::test_parse_header_returns_none_when_no_header_present PASSED
tests/test_parser.py::test_classify_origin_wordpress_org PASSED
tests/test_parser.py::test_classify_origin_commercial PASSED
tests/test_parser.py::test_classify_origin_custom PASSED
tests/test_parser.py::test_classify_origin_explicit_override_wins PASSED
tests/test_parser.py::test_classify_origin_unknown_when_no_header PASSED
7 passed in 0.07s
```

## 6. Agent: filesystem discovery (WP roots, plugins, MU plugins, drop-ins, max-depth)

**RED** — `python -m pytest tests/test_discover.py -v` (before `wp_estate_agent/discover.py` existed):

```
ModuleNotFoundError: No module named 'wp_estate_agent.discover'
1 error in 0.42s
```

**GREEN** — after implementing `discover.py`:

```
tests/test_discover.py::test_find_wordpress_roots_locates_wp_config PASSED
tests/test_discover.py::test_discover_plugins_classifies_all_kinds PASSED
tests/test_discover.py::test_find_wordpress_roots_respects_max_depth PASSED
3 passed in 0.10s
```

## 7. Agent: simulation payload, HTTP client, CLI wiring

**RED** (simulate) — `ModuleNotFoundError: No module named 'wp_estate_agent.simulate'`
**GREEN** (simulate) — 4 passed (schema shape, all origin/kind variants present, no
non-wordpress_org plugin ever marked `current`, distinct request ids per call).

**RED** (client) — `ModuleNotFoundError: No module named 'wp_estate_agent.client'`
**GREEN** (client, via `respx`-mocked HTTP) — 3 passed (auth headers sent correctly,
JSON body posted, distinct request id per call).

**RED** (cli) — `ModuleNotFoundError: No module named 'wp_estate_agent.cli'`
**GREEN** (cli, via Click's `CliRunner`) — 4 passed (`discover` prints JSON, `inventory
--simulate` prints a valid payload, `inventory --simulate --post` posts to a mocked
backend, `heartbeat` succeeds against a mocked backend).

**Full agent suite** — `python -m pytest tests/ -v`:

```
21 passed in 4.93s
```

**Lint** — `ruff check wp_estate_agent tests` → `All checks passed!`

---

## 8. Frontend: data-fetching hook, Sites page, lint, production build

**RED** — `npx vitest run tests/useApiResource.test.tsx` (before `src/api/useApiResource.ts` existed):

```
Error: Failed to resolve import "../src/api/useApiResource" from "tests/useApiResource.test.tsx".
Test Files  1 failed (1)
```

**GREEN** — after implementing `useApiResource.ts` (loading → data, loading → error states):

```
✓ tests/useApiResource.test.tsx (2 tests) 158ms
Test Files  1 passed (1)
     Tests  2 passed (2)
```

**RED** — `npx vitest run tests/SitesPage.test.tsx` (before `src/pages/SitesPage.tsx` existed):

```
Error: Failed to resolve import "../src/pages/SitesPage" from "tests/SitesPage.test.tsx".
Test Files  1 failed (1)
```

**GREEN** — after implementing `SitesPage.tsx` (renders loading text, then a table of fetched
sites, or a `role="alert"` error message on fetch failure):

```
✓ tests/SitesPage.test.tsx (2 tests) 202ms
Test Files  1 passed (1)
```

**Full frontend suite** — `npx vitest run`:

```
✓ tests/SitesPage.test.tsx (2 tests)
✓ tests/useApiResource.test.tsx (2 tests)
Test Files  2 passed (2)
     Tests  4 passed (4)
```

**Lint** — `npx eslint .` → no output (clean).

**Production build** — `npm run build` (`tsc -b && vite build`):

```
✓ 38 modules transformed.
dist/index.html                  0.40 kB │ gzip:  0.27 kB
dist/assets/index-C87zZLN-.css   0.83 kB │ gzip:  0.43 kB
dist/assets/index-CVCVsE8s.js  147.15 kB │ gzip: 47.27 kB
✓ built in 943ms
```

---

## 9. Compose integration and five installed WordPress sites

The first Compose run exposed three environment-specific failures, each reproduced from real logs before repair:

1. MariaDB 11 no longer ships `mysqladmin`; its health check exited 127. Replaced it with the image-supported `healthcheck.sh --connect --innodb_initialized`.
2. Existing local services occupied ports 8000 and 8081–8085. Preserved those unrelated containers and moved this MVP to API port 8001 and WordPress ports 8181–8185.
3. The WP-CLI bootstrap container did not inherit the `WORDPRESS_DB_*` environment consumed dynamically by the official `wp-config.php`. Added the database variables and selected each site's database in the bootstrap loop.

After the repairs, `docker compose up -d` completed successfully and the one-shot bootstrap finished with:

```
wp-bootstrap-1 | === wp5 bootstrap complete ===
wp-bootstrap-1 | All five sites bootstrapped.
wp-bootstrap-1 exited with code 0
```

HTTP and installation checks returned 200 and real WordPress page titles:

```
8181 200 WordPress Estate Demo — wp1
8182 200 WordPress Estate Demo — wp2
8183 200 WordPress Estate Demo — wp3
8184 200 WordPress Estate Demo — wp4
8185 200 WordPress Estate Demo — wp5
backend {"status":"ok"}
frontend 200
```

The simulated agent posted successfully:

```
{"http_status": 201, "sites_processed": 5}
```

API read-back proved:

```
5 sites
35 current plugin-installation observations
origins: commercial, custom, unknown, wordpress_org
kinds: dropin, mu-plugin, plugin
15 unknown-origin observations
```

Final smoke command, `.venv/Scripts/python.exe scripts/smoke.py`:

```
PASS backend: http://localhost:8001/health
PASS frontend: http://localhost:8080/
PASS wp1: http://localhost:8181/
PASS wp2: http://localhost:8182/
PASS wp3: http://localhost:8183/
PASS wp4: http://localhost:8184/
PASS wp5: http://localhost:8185/
PASS inventory: 5 sites, 35 plugins, 15 unknown-origin records
PASS compose config
```

Fresh post-fix quality gates:

- Backend: `25 passed, 1 warning`; Ruff passed.
- Agent: `23 passed`; Ruff passed.
- Frontend: `4 passed`; ESLint passed; production build passed.
- `docker compose config --quiet`: passed.

GNU Make is not installed on this Windows Git Bash host, so the Makefile targets were not invoked directly here; their underlying commands above were run successfully.

---

## 10. Independent review remediation

Cursor's first read-only review blocked the candidate because inventory request IDs were not aligned between the authenticated header and payload, and the unauthenticated MVP read API was published on all host interfaces. Claude Code implemented the replay-contract and CSV-export remediations test-first; Hermes independently completed the local-only port binding and frontend fallback correction.

The final behavior now proves:

- Inventory uses the same request ID in `X-Request-Id` and `payload.request_id`.
- Header/body mismatches return HTTP 400 without creating a site.
- Replaying an inventory request reuses the logical ID and returns HTTP 409.
- CSV cells beginning with `=`, `+`, `-`, or `@` are neutralized before export.
- Backend, frontend, and all five WordPress services bind to `127.0.0.1`.
- The frontend's non-build fallback points to API port 8001.

Post-remediation verification:

```
backend: 25 passed, 1 warning; Ruff passed
agent:   23 passed; Ruff passed
frontend: 4 passed; ESLint passed; production build passed
simulated production-client inventory post: HTTP 201, 5 sites processed
full smoke: API, UI, wp1-wp5, inventory, and Compose config passed
```

Runtime port inspection:

```
backend  127.0.0.1:8001->8000/tcp
frontend 127.0.0.1:8080->8080/tcp
wp1-wp5 127.0.0.1:8181-8185->80/tcp
```
