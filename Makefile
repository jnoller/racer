# Racer - Rapid deployment system for conda-projects
# Makefile for development and deployment automation

.PHONY: help setup clean install-dev test lint format

# Default target
help:
	@echo "Available targets:"
	@echo "  setup      - Create conda environment and install dependencies"
	@echo "  install-dev - Install development dependencies"
	@echo "  clean      - Remove conda environment"
	@echo "  test       - Run tests"
	@echo "  lint       - Run linting"
	@echo "  format     - Format code"
	@echo "  backend    - Run backend server"
	@echo "  client     - Install client in development mode"

# Setup conda environment and install dependencies
setup:
	@echo "Creating conda environment 'racer'..."
	conda create -n racer python=3.11 -y
	@echo "Activating environment and installing conda-project..."
	conda run -n racer conda install -c conda-forge conda-project -y
	@echo "Installing Python dependencies..."
	conda run -n racer pip install -r requirements.txt
	@echo "Setup complete! Activate the environment with: conda activate racer"

# Install development dependencies
install-dev: setup
	@echo "Installing development dependencies..."
	conda run -n racer pip install -r requirements-dev.txt
	@echo "Installing client in development mode..."
	conda run -n racer pip install -e src/client/

# Clean up conda environment
clean:
	@echo "Removing conda environment 'racer'..."
	conda env remove -n racer -y
	@echo "Environment removed."

# Run tests
test:
	@echo "Running tests..."
	conda run -n racer python -m pytest tests/

# Run linting
lint:
	@echo "Running linting..."
	conda run -n racer flake8 src/
	conda run -n racer black --check src/

# Format code
format:
	@echo "Formatting code..."
	conda run -n racer black src/

# Run backend server
backend:
	@echo "Starting backend server..."
	cd src/backend && conda run -n racer uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Install client in development mode
client:
	@echo "Installing client in development mode..."
	conda run -n racer pip install -e src/client/
	@echo "Client installed. Test with: racerctl --help"
