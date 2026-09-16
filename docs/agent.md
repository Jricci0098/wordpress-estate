# Host Agent

The agent is a Python CLI, not a WordPress plugin. It reads the filesystem, parses WordPress plugin headers, and sends versioned inventory to the central API.

## Commands

From the repository root:

```bash
# Generate demo JSON without posting
cd agent
PYTHONPATH=. ../.venv/Scripts/python.exe -m wp_estate_agent inventory --simulate

# Submit five simulated sites
PYTHONPATH=. ../.venv/Scripts/python.exe -m wp_estate_agent inventory \
  --simulate --post \
  --api-url http://localhost:8001 \
  --agent-id agent-demo \
  --agent-secret demo-agent-secret-change-me

# Discover real WordPress roots
PYTHONPATH=. ../.venv/Scripts/python.exe -m wp_estate_agent discover \
  --root /var/www --root /home --max-depth 8 --concurrency 4

# Heartbeat
PYTHONPATH=. ../.venv/Scripts/python.exe -m wp_estate_agent heartbeat \
  --api-url http://localhost:8001 \
  --agent-id agent-demo \
  --agent-secret demo-agent-secret-change-me
```

Equivalent environment variables are `WP_ESTATE_API_URL`, `WP_ESTATE_AGENT_ID`, and `WP_ESTATE_AGENT_SECRET`.

## Safety

The agent has no shell endpoint, update action, or arbitrary job execution. Discovery concurrency is bounded. A production installation should run under a dedicated low-privilege user and use a narrowly validated sudo wrapper only if per-site Unix-user execution is later required.
