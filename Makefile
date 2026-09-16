VENV_PYTHON := .venv/Scripts/python.exe
VENV_RUFF := .venv/Scripts/ruff.exe
API_URL ?= http://localhost:8001
AGENT_ID ?= agent-demo
AGENT_SECRET ?= demo-agent-secret-change-me

.PHONY: setup dev down test lint migrate seed demo smoke logs ps

setup:
	python -m venv .venv
	$(VENV_PYTHON) -m pip install -r backend/requirements-dev.txt -r agent/requirements-dev.txt
	cd frontend && npm ci

dev:
	docker compose up -d --build

down:
	docker compose down --remove-orphans

test:
	cd backend && ../$(VENV_PYTHON) -m pytest tests -q
	cd agent && ../$(VENV_PYTHON) -m pytest tests -q
	cd frontend && npm test

lint:
	cd backend && ../$(VENV_RUFF) check app tests
	cd agent && ../$(VENV_RUFF) check wp_estate_agent tests
	cd frontend && npm run lint
	docker compose config --quiet

migrate:
	docker compose exec backend alembic upgrade head

seed demo:
	cd agent && PYTHONPATH=. ../$(VENV_PYTHON) -m wp_estate_agent inventory --simulate --post --api-url $(API_URL) --agent-id $(AGENT_ID) --agent-secret $(AGENT_SECRET)

smoke:
	$(VENV_PYTHON) scripts/smoke.py

logs:
	docker compose logs -f --tail=200

ps:
	docker compose ps -a
