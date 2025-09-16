# `racer` - Rapid deployment system for conda-projects

Deploy conda-projects to Docker containers with a single command. Think Heroku/Fly.io for conda applications.

## What is Racer?

Racer is a deployment platform that takes your conda-projects and automatically:
- 🐳 **Builds Docker images** from your conda-project
- 🚀 **Deploys to containers** with one command
- 📈 **Scales horizontally** with Docker Swarm
- 🔄 **Load balances** across multiple instances
- 💾 **Persists state** across restarts

## Prerequisites

- [Conda](https://docs.conda.io/en/latest/miniconda.html) (Miniconda or Anaconda)
- [Docker](https://docs.docker.com/get-docker/)
- [Git](https://git-scm.com/downloads)

## Quick Start

Get up and running in 3 commands:

```bash
# 1. Clone and setup everything
git clone git@github.com:jnoller/racer.git
cd racer
make setup-all

# 2. Activate the environment
conda activate racer-dev

# 3. Deploy your first project
racerctl server start
racer deploy --project-name "my-app" --path /path/to/your/conda-project
```

**Done!** Your conda-project is now running in a Docker container.

---

## Getting Started

### First Time Setup

```bash
# Complete setup (creates environment, installs dependencies, initializes database)
make setup-all

# Activate the environment
conda activate racer-dev
```

### Daily Development

```bash
# Clean up generated files (preserves your environment)
make clean

# Start the backend server
racerctl server start

# Deploy your project
racer deploy --project-name "my-app" --path ./my-conda-project
```

### Fresh Start (if needed)

```bash
# Nuclear cleanup - removes everything including environments
make clean-all

# Start over
make setup-all
```

## Project Structure

```
racer/
├── README.md
├── Makefile                    # Development automation
├── pytest.ini                 # Test configuration
├── environments/               # Conda environment definitions
│   ├── base.yaml              # Base environment (production)
│   ├── dev.yaml               # Development environment
│   └── prod.yaml              # Production environment
├── src/
│   ├── backend/               # FastAPI orchestration server
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── docker_manager.py # Docker container management
│   │   ├── project_validator.py # Conda-project validation
│   │   ├── dockerfile_template.py # Dockerfile generation
│   │   ├── models.py         # SQLAlchemy database models
│   │   ├── database.py       # Database manager
│   │   └── racer.db          # SQLite database (auto-created)
│   └── client/               # Command line clients
│       ├── __init__.py
│       ├── api.py            # API client library
│       ├── racer_cli.py      # User-facing CLI (racer)
│       ├── cli.py            # Admin CLI (racerctl)
│       └── pyproject.toml     # Client installation
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

#### Deploy Projects

```bash
# Deploy a local project
racer deploy --project-name "my-app" --path ./my-project --app-port 8000

# Deploy from Git repository
racer deploy --project-name "my-app" --git https://github.com/user/repo.git --app-port 8000

# Deploy with custom environment variables
racer deploy --project-name "my-app" --path ./my-project --app-port 8000 \
  --environment DEBUG=true,API_KEY=secret123

# Deploy with custom command
racer deploy --project-name "my-app" --path ./my-project --app-port 8000 \
  --command "python app.py --port 8000"
```

#### Scale Projects

```bash
# Scale up: add instances (uses stored app port from deployment)
racer scale up --project-name "my-app" --instances 3

# Scale up: add one instance (default)
racer scale up --project-name "my-app"

# Scale down: remove instances (always keeps at least 1 running)
racer scale down --project-name "my-app" --instances 2

# Scale down: remove one instance (default)
racer scale down --project-name "my-app"
```

#### Dynamic Scaling

```bash
# Scale up by 5 instances
racer scale up --project-name "my-app" --instances 5

# Scale down by 3 instances
racer scale down --project-name "my-app" --instances 3

# Quick scale up by 1
racer scale up --project-name "my-app"

# Quick scale down by 1
racer scale down --project-name "my-app"
```

#### Redeploy Projects

```bash
# Redeploy with rebuilt image (includes source changes)
racer redeploy --project-name "my-app"

# Fast restart without rebuilding (configuration changes only)
racer redeploy --project-name "my-app" --no-rebuild

# Redeploy with new environment variables
racer redeploy --project-name "my-app" --environment DEBUG=true,LOG_LEVEL=debug

# Redeploy with new command
racer redeploy --project-name "my-app" --command "python app.py --debug"

# Redeploy a project
racer redeploy --project-name "my-app"

# List projects before redeploying
racer redeploy --list
```

#### Project Management

```bash
# Check project status
racer status --project-name "my-app"

# List all running projects
racer list

# Stop a project (works for both individual containers and swarm services)
racer stop --project-name "my-app"

# Stop without confirmation prompt
racer stop --project-name "my-app" --force

# Remove a project (admin command)
racerctl containers remove <container_id>
```

#### Validation and Utilities

```bash
# Validate a conda-project
racer validate --path ./my-project

# Validate from Git repository
racer validate --git https://github.com/user/repo.git

# Prepare for building (generate Dockerfile and show build instructions)
racer deploy --project-name "my-project" --path ./my-project --build-only
```

### Admin Commands (`racerctl`)

#### Server Management

```bash
# Start backend server (background by default)
racerctl server start

# Start in foreground mode
racerctl server start --foreground

# Start on specific port
racerctl server start --port 8002

# Stop server
racerctl server stop

# Force stop server
racerctl server stop --force

# Check server status
racerctl server status

# Restart server
racerctl server restart
```

#### Container Management

```bash
# List all containers
racerctl containers list

# View container logs
racerctl containers logs <container_id>

# Stop container
racerctl containers stop <container_id>

# Remove container
racerctl containers remove <container_id>

# Cleanup stopped containers
racerctl containers cleanup
```

#### Swarm Management

```bash
# Check swarm service status
racerctl swarm status --project-name "my-app"

# List all swarm services
racerctl swarm status

# View swarm service logs
racerctl swarm logs --project-name "my-app"

# Remove swarm service
racerctl swarm remove --project-name "my-app"

# Force remove without confirmation
racerctl swarm remove --project-name "my-app" --force
```

#### System Cleanup

```bash
# Clean up all projects, containers, and swarm services
racerctl cleanup-all

# Force cleanup without confirmation (use with caution!)
racerctl cleanup-all --force
```


## API

The backend provides a RESTful API at `http://localhost:8001` with comprehensive documentation:

### 📚 Interactive Documentation

- **Swagger UI**: [http://localhost:8001/docs](http://localhost:8001/docs) - Interactive API explorer
- **ReDoc**: [http://localhost:8001/redoc](http://localhost:8001/redoc) - Alternative documentation format  
- **OpenAPI Spec**: [http://localhost:8001/openapi.json](http://localhost:8001/openapi.json) - Machine-readable API specification
- **API Info**: [http://localhost:8001/api/info](http://localhost:8001/api/info) - Endpoint summary

### 🎯 API Structure

**User-facing endpoints** (`/api/v1/` - matches `racer` CLI):
- `POST /api/v1/deploy` - Deploy a conda-project
- `GET /api/v1/projects` - List all projects
- `POST /api/v1/status` - Get project status
- `POST /api/v1/redeploy` - Redeploy a project
- `POST /api/v1/scale` - Scale a project
- `POST /api/v1/validate` - Validate a conda-project

**Admin endpoints** (`/admin/` - matches `racerctl` CLI):
- `GET /admin/containers` - List all containers
- `POST /admin/containers/cleanup` - Cleanup containers
- `GET /admin/swarm/services` - List swarm services
- `GET /admin/swarm/service/{name}/status` - Get service status
- `GET /admin/swarm/service/{name}/logs` - Get service logs
- `DELETE /admin/swarm/service/{name}` - Remove service
- `POST /admin/cleanup-all` - Clean up all projects, containers, and services

**System endpoints** (`/`):
- `GET /` - API root information
- `GET /status` - Comprehensive status check (health, liveness, readiness, info)

## Port Management

Simple port management with automatic load balancing:

```bash
# Your app exposes port 8000 - we handle the rest!
racer deploy --project-name "my-app" --path ./project --app-port 8000

# Scale with automatic load balancing (uses stored app port)
racer scale up --project-name "my-app" --instances 3
```

**How it works:**
- You specify what port your app exposes (`--app-port 8000`)
- We auto-assign a host port (e.g., 8080) for load balancing
- Docker Swarm handles load balancing across all replicas
- All replicas accessible via the same host port (8080)

## Makefile Commands

Essential commands for development:

```bash
# Setup
make setup-all          # Complete setup (environment, dependencies, database)
make clean              # Clean generated files (preserves environment)
make clean-all          # Nuclear cleanup (removes everything)

# Development
make test               # Run tests
make lint               # Run linting
make format             # Format code

# Show all commands
make help
```

## Examples

```bash
# Deploy a project
racer deploy --project-name "my-app" --path ./my-project --app-port 8000

# Check status
racer status --project-name "my-app"

# Scale up
racer scale up --project-name "my-app" --instances 3

# Restart with new config
racer redeploy --project-name "my-app" --environment DEBUG=true
```

## Development

For development and testing:

Racer automatically initializes Docker Swarm mode when needed:
- Single-node swarm for development
- Multi-node swarm for production
- Automatic service creation and management

## Troubleshooting

Common issues and solutions:

```bash
# Server won't start
racerctl server stop --force
racerctl server start

# Environment issues
make clean-all
make setup-all

# Check what's running
racerctl server status
racer list
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License.
