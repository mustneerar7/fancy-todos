.PHONY: help format lint prestart dev migrate upgrade test clean

.DEFAULT_GOAL := help

help: ## Show this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

format: ## Auto-fix lint issues and format
	uv run bash scripts/format.sh

lint: ## Check formatting and lint (no mutations)
	uv run bash scripts/lint.sh

prestart: ## Apply migrations and seed first superuser
	uv run bash scripts/prestart.sh

dev: ## Run the dev server with auto-reload
	uv run fastapi dev app/main.py

migrate: ## Create a new alembic revision — usage: make migrate m="description"
	@if [ -z "$(m)" ]; then echo 'usage: make migrate m="description"'; exit 1; fi
	uv run alembic revision --autogenerate -m "$(m)"

upgrade: ## Apply pending migrations
	uv run alembic upgrade head

test: ## Run the pytest test suite with coverage
	uv run bash scripts/test.sh

clean: ## Remove Python and tool caches (keeps .venv)
	bash scripts/clean.sh
