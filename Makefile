# Verk Employee Management Extension Makefile
# Provides easy commands for testing, linting, and development tasks

# Python and UV executable
PYTHON = uv run python
UV = uv

# Directories
TEST_DIR = tests
SOURCE_DIR = source

# Coverage settings
COV_THRESHOLD = 80
COV_REPORT_DIR = htmlcov

# OS Detection
ifeq ($(OS),Windows_NT)
	DETECTED_OS := Windows
	RM := del /F /Q
	RMDIR := rmdir /S /Q
	WHICH := where
	NULL_DEVICE := NUL
	OPEN_CMD := start
else
	DETECTED_OS := $(shell uname -s)
	RM := rm -f
	RMDIR := rm -rf
	WHICH := which
	NULL_DEVICE := /dev/null
	ifeq ($(DETECTED_OS),Darwin)
		OPEN_CMD := open
	else
		OPEN_CMD := xdg-open
	endif
endif

# Default target
.PHONY: help
help:
	@echo "Verk Employee Management Extension"
	@echo "==================================="
	@echo ""
	@echo "Installation:"
	@echo "  install           Install all dependencies using uv"
	@echo "  install-tailwind  Install Tailwind CSS dependencies"
	@echo ""
	@echo "Development:"
	@echo "  dev               Run development server with auto-reload"
	@echo "  css               Quick Tailwind CSS rebuild (single run)"
	@echo "  tailwind          Watch and compile Tailwind CSS"
	@echo "  tailwind-build    Build Tailwind CSS for production (minified)"
	@echo ""
	@echo "Testing:"
	@echo "  test              Run all tests with coverage"
	@echo "  test-fast         Run tests without coverage"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  test-watch        Run tests in watch mode"
	@echo "  test-debug        Run tests with debug output"
	@echo ""
	@echo "Coverage:"
	@echo "  coverage          Generate and open coverage report"
	@echo "  coverage-report   Generate coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint              Run all linters"
	@echo "  format            Format code with black and isort"
	@echo "  type              Run mypy type checking"
	@echo "  ci                Run full CI pipeline locally"
	@echo ""
	@echo "Database:"
	@echo "  db-init           Initialize database with Alembic"
	@echo "  db-migrate        Create new migration"
	@echo "  db-upgrade        Apply migrations"
	@echo "  db-downgrade      Revert last migration"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean             Clean all generated files"
	@echo "  clean-pyc         Clean Python bytecode"
	@echo "  clean-test        Clean test artifacts"

# ========================================
# Installation
# ========================================

.PHONY: install
install:
	@echo "Detected OS: $(DETECTED_OS)"
	@echo "Installing uv if not already installed..."
	@$(WHICH) $(UV) >$(NULL_DEVICE) 2>&1 || (echo "Please install uv: https://docs.astral.sh/uv/getting-started/installation/")
	@echo "Syncing all dependencies with uv..."
	@$(UV) sync --group main --group dev

.PHONY: install-tailwind
install-tailwind:
	@echo "Installing Tailwind CSS dependencies..."
	@npm install

# ========================================
# Development
# ========================================

.PHONY: dev
dev: install
	@echo "Starting development server..."
	$(PYTHON) -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

.PHONY: css
css:
	@npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css

.PHONY: tailwind
tailwind:
	@echo "Watching Tailwind CSS..."
	@npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --watch

.PHONY: tailwind-build
tailwind-build:
	@echo "Building Tailwind CSS for production..."
	@npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# ========================================
# Testing
# ========================================

.PHONY: test
test: install
	@echo "Running all tests with coverage..."
	$(PYTHON) -m pytest $(TEST_DIR) \
		--cov=$(SOURCE_DIR) \
		--cov-report=term-missing \
		--cov-report=html:$(COV_REPORT_DIR) \
		--cov-fail-under=$(COV_THRESHOLD) \
		-v

.PHONY: test-fast
test-fast: install
	@echo "Running tests without coverage..."
	$(PYTHON) -m pytest $(TEST_DIR) -v

.PHONY: test-unit
test-unit: install
	@echo "Running unit tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -m unit -v

.PHONY: test-integration
test-integration: install
	@echo "Running integration tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -m integration -v

.PHONY: test-watch
test-watch: install
	@echo "Running tests in watch mode..."
	$(UV) run pytest-watch $(TEST_DIR) -- -x -v

.PHONY: test-debug
test-debug: install
	@echo "Running tests with debug output..."
	$(PYTHON) -m pytest $(TEST_DIR) \
		--log-cli-level=DEBUG \
		--capture=no \
		-vvv

.PHONY: test-employee
test-employee: install
	@echo "Running employee tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -m employee -v

.PHONY: test-time-entry
test-time-entry: install
	@echo "Running time entry tests..."
	$(PYTHON) -m pytest $(TEST_DIR) -m time_entry -v

# ========================================
# Coverage
# ========================================

.PHONY: coverage
coverage: test
	@echo "Opening coverage report..."
	@$(OPEN_CMD) $(COV_REPORT_DIR)/index.html || echo "Open $(COV_REPORT_DIR)/index.html manually"

.PHONY: coverage-report
coverage-report: install
	@echo "Generating coverage report..."
	$(PYTHON) -m pytest $(TEST_DIR) \
		--cov=$(SOURCE_DIR) \
		--cov-report=term-missing \
		--cov-report=html:$(COV_REPORT_DIR) \
		-q

# ========================================
# Code Quality
# ========================================

.PHONY: lint
lint: install
	@echo "Running ruff linter..."
	$(PYTHON) -m ruff check $(SOURCE_DIR) $(TEST_DIR)

.PHONY: format
format: install
	@echo "Formatting code with black and isort..."
	$(PYTHON) -m black $(SOURCE_DIR) $(TEST_DIR) --line-length=120
	$(PYTHON) -m isort $(SOURCE_DIR) $(TEST_DIR) --profile=black --line-length=120

.PHONY: type
type: install
	@echo "Running MyPy type checker..."
	$(PYTHON) -m mypy $(SOURCE_DIR) --ignore-missing-imports || true

.PHONY: ci
ci: install
	@echo "=========================================="
	@echo "Running CI Pipeline"
	@echo "=========================================="
	@echo ""
	@echo "Step 1: Check code formatting..."
	@$(PYTHON) -m black --check --line-length=120 $(SOURCE_DIR) $(TEST_DIR) || (echo "Run 'make format' to fix" && exit 1)
	@echo "Passed: black"
	@echo ""
	@echo "Step 2: Check import sorting..."
	@$(PYTHON) -m isort --check-only --profile=black --line-length=120 $(SOURCE_DIR) $(TEST_DIR) || (echo "Run 'make format' to fix" && exit 1)
	@echo "Passed: isort"
	@echo ""
	@echo "Step 3: Run linter..."
	@$(PYTHON) -m ruff check $(SOURCE_DIR) $(TEST_DIR)
	@echo "Passed: ruff"
	@echo ""
	@echo "Step 4: Run tests..."
	@$(PYTHON) -m pytest $(TEST_DIR) \
		--cov=$(SOURCE_DIR) \
		--cov-report=term \
		--cov-fail-under=$(COV_THRESHOLD) \
		-v
	@echo ""
	@echo "=========================================="
	@echo "CI Pipeline Passed!"
	@echo "=========================================="

# ========================================
# Database
# ========================================

.PHONY: db-init
db-init: install
	@echo "Initializing Alembic..."
	$(PYTHON) -m alembic init alembic

.PHONY: db-migrate
db-migrate: install
ifndef MSG
	$(error MSG not specified. Usage: make db-migrate MSG="migration description")
endif
	@echo "Creating new migration..."
	$(PYTHON) -m alembic revision --autogenerate -m "$(MSG)"

.PHONY: db-upgrade
db-upgrade: install
	@echo "Applying migrations..."
	$(PYTHON) -m alembic upgrade head

.PHONY: db-downgrade
db-downgrade: install
	@echo "Reverting last migration..."
	$(PYTHON) -m alembic downgrade -1

.PHONY: db-history
db-history: install
	@echo "Migration history..."
	$(PYTHON) -m alembic history

# ========================================
# Cleanup
# ========================================

.PHONY: clean
clean: clean-pyc clean-test
	@echo "Cleaning all generated files..."
	@$(RMDIR) build dist *.egg-info 2>$(NULL_DEVICE) || true
	@$(RMDIR) node_modules 2>$(NULL_DEVICE) || true
	@echo "Clean complete"

.PHONY: clean-pyc
clean-pyc:
	@echo "Cleaning Python bytecode..."
	@find . -type f -name "*.py[cod]" -delete 2>$(NULL_DEVICE) || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>$(NULL_DEVICE) || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>$(NULL_DEVICE) || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>$(NULL_DEVICE) || true

.PHONY: clean-test
clean-test:
	@echo "Cleaning test artifacts..."
	@$(RMDIR) .pytest_cache $(COV_REPORT_DIR) .coverage 2>$(NULL_DEVICE) || true
	@$(RM) coverage.xml test-results.xml 2>$(NULL_DEVICE) || true
