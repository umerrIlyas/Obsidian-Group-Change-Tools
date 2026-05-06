.PHONY: help install dev-api dev-web db-up db-down db-logs migrate makemigration test lint format typecheck eval reembed clean

help:
	@echo "ChangeTools — make targets"
	@echo ""
	@echo "  make install         Install backend + frontend deps"
	@echo "  make dev-api         Run FastAPI dev server (port 8000)"
	@echo "  make dev-web         Run Next.js dev server (port 3000)"
	@echo "  make db-up           Start Postgres + pgvector via docker compose"
	@echo "  make db-down         Stop Postgres"
	@echo "  make db-logs         Tail Postgres logs"
	@echo "  make migrate         Apply Alembic migrations"
	@echo "  make makemigration m='msg'  Generate a new migration"
	@echo "  make test            Run backend + frontend tests"
	@echo "  make lint            Lint everything"
	@echo "  make format          Format everything"
	@echo "  make typecheck       Type-check everything"
	@echo "  make eval            Run the eval harness"
	@echo "  make reembed         Re-embed all chunks (after embedding-provider swap)"
	@echo "  make clean           Remove build artifacts"

install:
	cd apps/api && uv sync
	cd apps/web && pnpm install

dev-api:
	cd apps/api && uv run uvicorn changetools.main:app --reload --host 0.0.0.0 --port 8000

dev-web:
	cd apps/web && pnpm dev

db-up:
	docker compose up -d postgres
	@echo "Waiting for Postgres to be ready..."
	@until docker compose exec -T postgres pg_isready -U changetools >/dev/null 2>&1; do sleep 0.5; done
	@echo "Postgres is ready on localhost:5432"

db-down:
	docker compose down

db-logs:
	docker compose logs -f postgres

migrate:
	cd apps/api && uv run alembic upgrade head

makemigration:
	cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

test:
	cd apps/api && uv run pytest
	cd apps/web && pnpm test --if-present

lint:
	cd apps/api && uv run ruff check src tests
	cd apps/web && pnpm lint

format:
	cd apps/api && uv run ruff format src tests
	cd apps/web && pnpm format

typecheck:
	cd apps/api && uv run mypy src
	cd apps/web && pnpm typecheck

eval:
	cd apps/api && uv run python -m changetools.eval
	@echo "See eval_report.md for results."

reembed:
	cd apps/api && uv run python -m changetools.scripts.reembed

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf apps/web/.next apps/web/.turbo
