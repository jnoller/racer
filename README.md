# `racer` - Rapid deployment system for conda-projects

## Summary

`racer` is a comprehensive deployment platform that simplifies the process of deploying conda-based applications to containerized environments. The system consists of:

1. **Backend Orchestration API** (FastAPI) - A Heroku/Fly.io-like REST API server that deploys `conda-project` based applications to Docker containers
2. **Dual CLI Interface**:
   - `racer` - User-facing commands for running and managing projects
   - `racerctl` - Admin commands for container and service management

## Features

- 🚀 **One-command deployment** of conda-projects to Docker containers
- 🐳 **Docker integration** with automatic image building and container management
- 📦 **Conda-project support** with validation and environment management
- 🔧 **Dual CLI interface** for users and administrators
- 🌐 **RESTful API** with health, validation, and container management endpoints
- 🧪 **Comprehensive testing** with unit and integration tests
- 📊 **Coverage reporting** and automated testing
- ⚡ **Fast development** with hot-reload and development tools

## Prerequisites

Before getting started, ensure you have the following installed on your system:

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Docker](https://docs.docker.com/get-docker/) (for container management)
- [Git](https://git-scm.com/downloads) (for version control)

## Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd racer
```

### 2. Automated Setup (Recommended)

Use the provided Makefile for easy setup:

```bash
# Create conda environment and install all dependencies
make setup

# Install development dependencies and client
make install-dev

# Activate the environment
conda activate racer
```

### 3. Start the Backend Server

```bash
# Start the API server
make backend

# Or run directly
cd src/backend && conda run -n racer python main.py
```

### 4. Test the Installation

```bash
# Test the API health
curl http://localhost:8000/health

# Test the CLI
racer --help
racerctl --help
```

## Project Structure

```
racer/
├── README.md
├── Makefile                    # Development automation
├── pytest.ini                 # Test configuration
├── requirements.txt            # Main Python dependencies
├── requirements-dev.txt        # Development dependencies
├── src/
│   ├── backend/               # FastAPI orchestration server
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── docker_manager.py # Docker container management
│   │   ├── project_validator.py # Conda-project validation
│   │   └── dockerfile_template.py # Dockerfile generation
│   └── client/               # Command line clients
│       ├── __init__.py
│       ├── api.py            # API client library
│       ├── racer_cli.py      # User-facing CLI (racer)
│       ├── cli.py            # Admin CLI (racerctl)
│       └── setup.py          # Client installation
├── tests/                    # Test suite
│   ├── test_basic.py         # Basic functionality tests
│   ├── test_integration_simple.py # Integration tests
│   ├── conftest.py          # Test fixtures
│   └── README.md            # Test documentation
└── test-project/            # Sample conda-project for testing
    ├── conda-project.yml
    ├── environment.yml
    └── main.py
```

## CLI Commands

### User Commands (`racer`)

```bash
# Run a conda-project in Docker
racer run --path /path/to/project --ports 8080:8000

# Validate a conda-project
racer validate --path /path/to/project

# Generate Dockerfile for a project
racer dockerfile --path /path/to/project

# Check project status
racer status                    # Check status of running projects
racer status --list            # List all running containers
racer status --container-id <id>  # Check specific container
```

### Admin Commands (`racerctl`)

```bash
# Health and status
racerctl health
racerctl liveness
racerctl readiness
racerctl info

# Container management
racerctl containers list
racerctl containers status <container_id>
racerctl containers logs <container_id>
racerctl containers stop <container_id>
racerctl containers remove <container_id>
racerctl containers cleanup
```

## API Endpoints

The backend provides a RESTful API at `http://localhost:8000`:

### Health & Status
- `GET /` - API information
- `GET /health` - Health check
- `GET /liveness` - Liveness probe
- `GET /ready` - Readiness probe

### Project Management
- `POST /validate` - Validate conda-project
- `POST /dockerfile` - Generate Dockerfile
- `POST /run` - Build and run project (legacy)
- `POST /project/status` - Get comprehensive project status

### Container Management
- `POST /containers/run` - Run container
- `GET /containers` - List containers
- `GET /containers/{id}/status` - Container status
- `GET /containers/{id}/logs` - Container logs
- `POST /containers/{id}/stop` - Stop container
- `DELETE /containers/{id}` - Remove container
- `POST /containers/cleanup` - Cleanup stopped containers

## Makefile Commands

The project includes a comprehensive Makefile for development:

```bash
# Show all available commands
make help

# Setup and installation
make setup              # Create conda environment and install dependencies
make install-dev        # Install development dependencies and client

# Development
make backend           # Run backend server
make client            # Install client in development mode

# Testing
make test              # Run all tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests only
make test-quick        # Run quick tests (no Docker/API)
make test-coverage     # Run tests with coverage report

# Code quality
make lint              # Run linting
make format            # Format code

# Cleanup
make clean             # Remove conda environment
```

## Usage Examples

### 1. Deploy a Local Project

```bash
# Start the backend server
make backend

# In another terminal, run your project
racer run --path /path/to/your/conda-project --ports 8080:8000
```

### 2. Deploy from Git Repository

```bash
racer run --git https://github.com/user/repo.git --ports 8080:8000
```

### 3. Validate a Project

```bash
# Validate local project
racer validate --path /path/to/project

# Validate git repository
racer validate --git https://github.com/user/repo.git
```

### 4. Generate Dockerfile

```bash
# Generate Dockerfile for a project
racer dockerfile --path /path/to/project --output ./Dockerfile
```

### 5. Check Project Status

```bash
# Check status of running projects
racer status

# List all running containers
racer status --list

# Check specific container status
racer status --container-id <container_id>
```

### 6. Container Management

```bash
# List running containers
racerctl containers list

# View container logs
racerctl containers logs <container_id>

# Stop a container
racerctl containers stop <container_id>
```

## Testing

The project includes comprehensive testing infrastructure:

### Running Tests

```bash
# Run all tests
make test

# Run specific test types
make test-unit         # Unit tests
make test-integration  # Integration tests
make test-quick        # Quick tests (no Docker/API)

# Run with coverage
make test-coverage
```

### Test Structure

- **Unit Tests**: Test individual functions and classes
- **Integration Tests**: Test API endpoints and full workflows
- **Coverage**: HTML coverage reports in `htmlcov/`

## Configuration

### Environment Variables

```bash
# API Configuration
export RACER_API_URL=http://localhost:8000
export RACER_API_TIMEOUT=30

# Docker Configuration
export DOCKER_HOST=unix:///var/run/docker.sock
```

### Backend Configuration

Create a `.env` file in the `src/backend` directory:

```bash
# API configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True

# Docker configuration
DOCKER_HOST=unix:///var/run/docker.sock
```

## Dependencies

### Core Dependencies
- **FastAPI** - Web framework for the API
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation
- **Click** - CLI framework
- **Requests** - HTTP client
- **Docker** - Docker SDK for Python
- **GitPython** - Git repository management
- **PyYAML** - YAML parsing

### Development Dependencies
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **black** - Code formatting
- **flake8** - Linting
- **mypy** - Type checking

## Troubleshooting

### Common Issues

1. **Docker not running**: Start Docker Desktop or Docker daemon
2. **Port conflicts**: Change the API port in configuration
3. **Permission issues**: Ensure your user has Docker permissions
4. **Import errors**: Ensure PYTHONPATH is set correctly

### Getting Help

```bash
# Check API health
curl http://localhost:8000/health

# Check CLI help
racer --help
racerctl --help

# View container status
racerctl containers list

# Check logs
racerctl containers logs <container_id>
```

### Debug Mode

```bash
# Run with verbose output
racer --verbose run --path /path/to/project
racerctl --verbose containers list
```

## Development

### Setting up Development Environment

```bash
# Clone and setup
git clone <repository-url>
cd racer
make setup
make install-dev

# Start backend in development mode
make backend

# Run tests
make test
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Run type checking
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `make test`
6. Submit a pull request

## License

[Add your license information here]

## Changelog

### v0.1.0
- Initial release
- FastAPI backend with health endpoints
- Dual CLI interface (racer/racerctl)
- Docker integration with container management
- Conda-project validation and deployment
- Comprehensive testing infrastructure
- Development automation with Makefile