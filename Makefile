ACTIVATE := . .venv/bin/activate

define run_checks
	exit_code=0; \
	cd $1; \
	echo "Running poetry check"; \
	poetry check || exit_code=$$?;\
	echo "Running mypy"; \
	mypy . --exclude '/\.venv/' || exit_code=$$?; \
	echo "Running ruff"; \
	ruff check . || exit_code=$$?; \
	echo "Running black"; \
	black --check . || exit_code=$$?; \
	if [ $$exit_code -eq 1 ]; then \
		echo "\033[0;31mOne or more checks failed with exit code $$exit_code\033[0m"; \
	else \
		echo "\033[0;32mAll checks executed successfully.\033[0m"; \
	fi; \
	exit $$exit_code
endef


.PHONY: help install install-dev test test-cov lint format type-check clean build publish

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install the package in development mode
	poetry install

install-dev: ## Install development dependencies
	poetry install --with dev

test: ## Run tests
	poetry run pytest

test-cov: ## Run tests with coverage
	poetry run pytest --cov=jsonapi --cov-report=html --cov-report=term-missing

lint:
	@$(ACTIVATE) && \
	$(call run_checks,.)

lint/fix:
	@$(ACTIVATE) && \
	black .
	ruff check --fix .

format: ## Format code
	@$(ACTIVATE) && \
	black .
	ruff check --fix .

type-check: ## Run type checking
	@$(ACTIVATE) && \
	mypy . --exclude '/\.venv/'

check: ## Run all checks (lint, type-check, test)
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test

clean: ## Clean build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

build: ## Build the package
	poetry build

publish: ## Publish to PyPI (requires authentication)
	poetry publish

pre-commit-install: ## Install pre-commit hooks
	poetry run pre-commit install

pre-commit-run: ## Run pre-commit on all files
	poetry run pre-commit run --all-files

changelog: ## Generate changelog from git commits
	python scripts/changelog.py update

changelog-preview: ## Preview changelog without writing to file
	python scripts/changelog.py preview

version: ## Show current version
	@poetry version -s

bump-patch: ## Bump patch version
	poetry version patch

bump-minor: ## Bump minor version
	poetry version minor

bump-major: ## Bump major version
	poetry version major

release: ## Prepare a new release (bump version, update changelog)
	@echo "Preparing new release..."
	@read -p "Enter release type (patch/minor/major): " release_type; \
	case $$release_type in \
		patch) $(MAKE) bump-patch ;; \
		minor) $(MAKE) bump-minor ;; \
		major) $(MAKE) bump-major ;; \
		*) echo "Invalid release type. Use patch, minor, or major."; exit 1 ;; \
	esac
	$(MAKE) changelog
	@echo "Release prepared! Review CHANGELOG.md and commit changes."

create-release: ## Create a new release with version
	@read -p "Enter version (e.g., 0.2.0): " version; \
	python scripts/changelog.py release --version $$version

release-tag: ## Create a release tag and push to trigger GitHub Action
	@read -p "Enter version (e.g., 0.2.0): " version; \
	git tag v$$version; \
	git push origin v$$version; \
	echo "Tag v$$version created and pushed. GitHub Action will automatically release to PyPI."

test-release: ## Create a test release tag for TestPyPI
	@read -p "Enter version (e.g., 0.2.0-alpha.1): " version; \
	git tag v$$version; \
	git push origin v$$version; \
	echo "Test tag v$$version created and pushed. GitHub Action will automatically release to TestPyPI."
