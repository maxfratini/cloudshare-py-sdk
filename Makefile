.DEFAULT_GOAL := help
.PHONY: help setup lock sync test lint fmt check build dist dist-bundle build-onefile clean

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

setup: ## Create the venv and install every group
	uv sync --all-groups

lock: ## Refresh uv.lock
	uv lock

sync: ## Sync the venv to uv.lock (no re-locking)
	uv sync --all-groups --locked

test: ## Run the test suite
	uv run pytest

lint: ## Lint
	uv run ruff check .

fmt: ## Autofix lint issues
	uv run ruff check --fix .

check: lint test ## Lint + test

build: dist ## Alias for dist

dist: ## Build a standalone binary for the host OS
	uv run nuitka main.py

build-onefile: ## Build a single-file binary for the host OS
	uv run nuitka --mode=onefile main.py

dist-bundle: ## Build a macOS .app bundle (single-file + bundle)
	uv run nuitka --mode=onefile --macos-create-app-bundle main.py

clean: ## Remove build artifacts and the venv
	rm -rf build dist *.dist-info .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +