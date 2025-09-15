# Racer - Rapid deployment system for conda-projects
# Makefile for development and deployment automation

.PHONY: help setup clean install-dev test test-unit test-integration test-docker test-api test-coverage test-quick lint format db-init db-clean db-reset

# Default target
help:
	@echo "Available targets:"
	@echo "  setup         - Create conda environment and install dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  clean         - Remove conda environment"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-docker   - Run Docker tests only"
	@echo "  test-api      - Run API tests only"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  test-quick    - Run quick tests (no Docker/API)"
	@echo "  lint          - Run linting"
	@echo "  format        - Format code"
	@echo "  backend       - Run backend server"
	@echo "  client        - Install client in development mode"
	@echo "  db-init       - Initialize database"
	@echo "  db-clean      - Clean up database (remove all data)"
	@echo "  db-reset      - Reset database (drop and recreate)"

# Setup conda environment and install dependencies
setup:
	@echo "Creating conda environment from base.yaml..."
	conda env create -f environments/base.yaml
	@echo "Installing client in development mode..."
	conda run -n racer pip install -e src/client/
	@echo "Setup complete! Activate the environment with: conda activate racer"

# Install development dependencies
install-dev:
	@echo "Creating development environment from dev.yaml..."
	conda env create -f environments/dev.yaml
	@echo "Installing client in development mode..."
	conda run -n racer-dev pip install -e src/client/
	@echo "Development setup complete! Activate with: conda activate racer-dev"

# Clean up conda environments
clean:
	@echo "Removing conda environments..."
	conda env remove -n racer -y 2>/dev/null || true
	conda env remove -n racer-dev -y 2>/dev/null || true
	conda env remove -n racer-prod -y 2>/dev/null || true
	@echo "Environments removed."

# Run tests
test:
	@echo "Running all tests..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/test_basic.py -v

test-unit:
	@echo "Running unit tests..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/unit/ -v

test-integration:
	@echo "Running integration tests..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/test_integration_simple.py -v

test-docker:
	@echo "Running Docker tests..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/ -v -m docker

test-api:
	@echo "Running API tests..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/ -v -m api

test-coverage:
	@echo "Running tests with coverage..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/test_basic.py --cov=src --cov-report=html --cov-report=term

test-quick:
	@echo "Running quick tests (no Docker/API)..."
	PYTHONPATH=$(PWD) conda run -n racer-dev python -m pytest tests/test_basic.py -v

# Run linting
lint:
	@echo "Running linting..."
	conda run -n racer-dev flake8 src/
	conda run -n racer-dev black --check src/

# Format code
format:
	@echo "Formatting code..."
	conda run -n racer-dev black src/

# Run backend server
backend:
	@echo "Starting backend server..."
	cd src/backend && conda run -n racer-dev uvicorn main:app --reload --host 0.0.0.0 --port 8001

# Install client in development mode
client:
	@echo "Installing client in development mode..."
	conda run -n racer-dev pip install -e src/client/
	@echo "Client installed. Test with: racerctl --help"

# Database management
db-init:
	@echo "Initializing database..."
	cd src/backend && PYTHONPATH=$(PWD) conda run -n racer-dev python -c "import sys; sys.path.append('.'); from database import DatabaseManager; db = DatabaseManager(); db.init_database(); print('Database initialized successfully')"

db-clean:
	@echo "Cleaning up database..."
	cd src/backend && PYTHONPATH=$(PWD) conda run -n racer-dev python -c "import sys; sys.path.append('.'); from database import DatabaseManager; db = DatabaseManager(); db.cleanup_database(); print('Database cleaned successfully')"

db-reset: db-clean db-init
	@echo "Database reset complete"
