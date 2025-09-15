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
- 🆔 **Auto-generated project IDs** with user-friendly project names for easy management
- 🔧 **Dual CLI interface** for users and administrators
- 🌐 **RESTful API** with health, validation, and container management endpoints
- 📈 **Horizontal scaling** with Docker Compose for multiple instances
- 🔄 **Load balancing ready** with Nginx configuration generation
- 💾 **SQLite persistence** for project and container state tracking
- 🔄 **State persistence** across backend restarts
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

# Initialize the database
make db-init

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
│   │   ├── dockerfile_template.py # Dockerfile generation
│   │   ├── compose_template.py # Docker Compose template generation
│   │   ├── models.py         # SQLAlchemy database models
│   │   ├── database.py       # Database manager
│   │   └── racer.db          # SQLite database (auto-created)
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
racer run --project-name "my-app" --path /path/to/project --ports 8080:8000

# Validate a conda-project
racer validate --path /path/to/project

# Generate Dockerfile for a project
racer dockerfile --path /path/to/project

# List running projects
racer list-projects            # List all running projects

# Check project status
racer status                   # Check status of running projects
racer status --project-id <id> # Check specific project by ID
racer status --list            # List all running projects

# Scale a project to multiple instances
racer scale --project-name <name> --instances <n> --path <path>  # Scale local project
racer scale --project-name <name> --instances <n> --git <url>    # Scale from git repo
racer scale --project-name <name> --instances 3 --ports 8001:8000 # Scale with port mapping

# Rerun a project
racer rerun                    # Rerun with rebuilt image (includes source changes)
racer rerun --no-rebuild       # Rerun with existing image (faster restart)
racer rerun --project-id <id>  # Rerun specific project by ID
racer rerun --project-name <name>  # Rerun all instances of project by name
racer rerun --list             # List projects before rerunning
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
- `GET /projects` - List all running projects
- `POST /project/status` - Get comprehensive project status by container ID
- `POST /project/status-by-id` - Get comprehensive project status by project ID
- `POST /project/rerun` - Rerun a project by stopping and restarting container
- `POST /project/scale` - Scale a project to multiple instances

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

# Database management
make db-init            # Initialize database
make db-clean           # Clean up database (remove all data)
make db-reset           # Reset database (drop and recreate)

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

## Database Management

Racer uses SQLite for persistent state tracking across backend restarts. The database automatically tracks:

- **Projects** - Project metadata, paths, and configurations
- **Containers** - Container IDs, names, status, ports, and environment variables
- **Scale Groups** - Docker Compose deployments and scaling information

### Database Commands

```bash
# Initialize the database (run after setup)
make db-init

# Clean up database (remove all data)
make db-clean

# Reset database (drop and recreate)
make db-reset
```

### Database Features

- **Automatic initialization** - Database is created on first backend startup
- **State persistence** - Container and project state survives backend restarts
- **Foreign key relationships** - Proper data integrity between projects and containers
- **JSON storage** - Port mappings and environment variables stored as JSON
- **Automatic cleanup** - Stopped containers can be cleaned up automatically

The database file (`src/backend/racer.db`) is automatically created and managed. It's included in `.gitignore` to avoid committing database state to version control.

## Project Management

Racer uses a dual-identifier system for managing projects:

### Project Names vs Project IDs

- **Project Name** (`--project-name`): User-provided, memorable name for the project (required for `racer run`)
- **Project ID**: Auto-generated unique identifier (UUID) created by the backend

### How It Works

1. **Running Projects**: Users provide a `--project-name` when running projects
2. **Auto-Generation**: Backend automatically generates a unique `project_id` using UUID
3. **Flexible Reference**: Users can reference projects by either `--project-name` OR `--project-id` for all operations

### Example Workflow

```bash
# Run a project with a name
racer run --project-name "my-app" --path ./my-project

# Backend generates: project_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"

# Reference by name
racer status --project-name "my-app"
racer rerun --project-name "my-app"

# Reference by ID (from list-projects output)
racer status --project-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
racer rerun --project-id "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
```

### Benefits

- **User-Friendly**: Use memorable project names for daily operations
- **Unique Identification**: Auto-generated IDs ensure no conflicts
- **Flexible Management**: Choose the identifier that works best for your workflow
- **Persistent Tracking**: Project state survives backend restarts

## Usage Examples

### 1. Deploy a Local Project

```bash
# Start the backend server
make backend

# In another terminal, run your project
racer run --project-name "my-app" --path /path/to/your/conda-project --ports 8080:8000
```

### 2. Deploy from Git Repository

```bash
racer run --project-name "my-app" --git https://github.com/user/repo.git --ports 8080:8000
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

### 5. List and Check Project Status

```bash
# List all running projects
racer list-projects

# Check status of running projects
racer status

# Check specific project status
racer status --project-id <project_id>

# List projects with status command
racer status --list
```

### 6. Scale Projects

```bash
# Scale a local project to 3 instances
racer scale --project-name my-app --instances 3 --path ./my-project

# Scale from git repository
racer scale --project-name my-app --instances 5 --git https://github.com/user/repo

# Scale with custom port mapping (auto-increments host ports)
racer scale --project-name my-app --instances 3 --ports 8001:8000

# Scale with custom configuration
racer scale --project-name my-app --instances 2 --path ./my-project \
  --ports 8001:8000 --environment DEBUG=true --command "python app.py"
```

**Scale Behavior:**
- **Docker Compose orchestration**: Uses Docker Compose for reliable multi-container management
- **Multiple instances**: Creates multiple containers from the same project
- **Port management**: Auto-increments host ports (8001, 8002, 8003, etc.)
- **Project naming**: Uses project name for container naming with unique suffixes
- **Load balancing ready**: Each instance gets unique ports for load balancer setup
- **Service management**: Automatic health checks and restart policies
- **Generated files**: Creates `docker-compose.yml` and optional `nginx.conf` for load balancing

### 7. Rerun Projects

```bash
# Rerun with rebuilt image (includes source changes)
racer rerun

# Rerun with existing image (faster restart)
racer rerun --no-rebuild

# Rerun specific project with rebuilt image
racer rerun --project-id <project_id>

# Rerun all instances of a project by name
racer rerun --project-name my-app

# Rerun with custom configuration and rebuilt image
racer rerun --project-id <project_id> --ports 8080:8000 --environment DEBUG=true

# Fast restart without rebuilding (for configuration changes only)
racer rerun --project-id <project_id> --no-rebuild

# Rerun all instances of a project without rebuilding
racer rerun --project-name my-app --no-rebuild

# List projects before rerunning
racer rerun --list
```

**Rerun Behavior:**
- **Default (`racer rerun`)**: Rebuilds Docker image with updated source files - perfect for code changes
- **Fast restart (`racer rerun --no-rebuild`)**: Restarts with existing image - ideal for configuration changes only
- **Project name support**: Use `--project-name` to rerun all instances of a scaled project
- **Project ID support**: Use `--project-id` to rerun a specific instance
- **Source file detection**: Automatically finds project source and rebuilds with latest changes
- **Configuration preservation**: Maintains original ports, environment, and commands unless overridden
- **Multi-instance handling**: When using `--project-name`, reruns all instances of that project

### 7. Container Management

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
- **Docker Compose** - Multi-container orchestration
- **SQLAlchemy** - Database ORM
- **Alembic** - Database migrations

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
- Horizontal scaling with Docker Compose
- Load balancing with Nginx configuration
- **SQLite database integration** for persistent state tracking
- **Database management commands** (db-init, db-clean, db-reset)
- **State persistence** across backend restarts
- Comprehensive testing infrastructure
- Development automation with Makefile