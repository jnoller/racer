# Racer - Rapid deployment system for conda-projects
# Makefile for development and deployment automation

.PHONY: help setup setup-all verify clean install-dev test test-unit test-integration test-docker test-api test-coverage test-quick lint format db-init db-clean db-reset

# Default target
help:
	@echo "Available targets:"
	@echo "  setup-all     - Complete setup: environment, dependencies, database, and verification"
	@echo "  setup         - Create conda environment and install dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  verify        - Verify that everything is working correctly"
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

# Complete setup: environment, dependencies, database, and verification
setup-all:
	@echo "🚀 Starting complete Racer setup..."
	@echo ""
	@echo "Step 1/6: Cleaning up any existing environments..."
	@$(MAKE) clean
	@echo ""
	@echo "Step 2/6: Creating development environment..."
	@$(MAKE) install-dev
	@echo ""
	@echo "Step 3/6: Initializing database..."
	@$(MAKE) db-init
	@echo ""
	@echo "Step 4/6: Running quick verification tests..."
	@$(MAKE) test-quick
	@echo ""
	@echo "Step 5/6: Checking Docker availability..."
	@docker --version > /dev/null 2>&1 && echo "✅ Docker is available" || echo "⚠️  Docker not found - some features may not work"
	@echo ""
	@echo "Step 6/6: Setup verification complete!"
	@echo ""
	@echo "🎉 Racer is ready to use!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Activate the environment: conda activate racer-dev"
	@echo "  2. Start the backend: make backend"
	@echo "  3. In another terminal, test the CLI: racer --help"
	@echo "  4. Try running a project: racer run --project-name test --path ./test-project"
	@echo ""

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

# Quick verification that everything is working
verify:
	@echo "🔍 Verifying Racer setup..."
	@echo ""
	@echo "Checking conda environment..."
	@conda info --envs | grep -q "racer-dev" && echo "✅ racer-dev environment exists" || echo "❌ racer-dev environment not found"
	@echo ""
	@echo "Checking CLI installation..."
	@conda run -n racer-dev racer --help > /dev/null 2>&1 && echo "✅ CLI is working" || echo "❌ CLI not working"
	@echo ""
	@echo "Checking database..."
	@cd src/backend && PYTHONPATH=$(PWD) conda run -n racer-dev python -c "import sys; sys.path.append('.'); from database import DatabaseManager; db = DatabaseManager(); print('✅ Database is accessible')" 2>/dev/null || echo "❌ Database not accessible"
	@echo ""
	@echo "Checking Docker..."
	@docker --version > /dev/null 2>&1 && echo "✅ Docker is available" || echo "⚠️  Docker not found"
	@echo ""
	@echo "Running quick tests..."
	@$(MAKE) test-quick > /dev/null 2>&1 && echo "✅ Tests are passing" || echo "❌ Tests are failing"
	@echo ""
	@echo "🎯 Verification complete!"
