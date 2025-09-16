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

# 2. Start working (choose one)
make shell                    # Interactive shell with environment activated
# OR
conda activate racer-dev      # Manual activation

# 3. Deploy your first project
racerctl server start
racer run --project-name "my-app" --path /path/to/your/conda-project
```

**Done!** Your conda-project is now running in a Docker container.

---

## Getting Started

### First Time Setup

```bash
# Complete setup (creates environment, installs dependencies, initializes database)
make setup-all

# Start working immediately
make shell
```

### Daily Development

```bash
# Clean up generated files (preserves your environment)
make clean

# Start the backend server
racerctl server start

# Deploy your project
racer run --project-name "my-app" --path ./my-conda-project
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

### Essential Commands

```bash
# Deploy your project
racer run --project-name "my-app" --path ./my-project --app-port 8000

# Check status
racer status --project-name "my-app"

# Scale up
racer scale --project-name "my-app" --instances 3 --app-port 8000

# Restart with new config
racer rerun --project-name "my-app" --environment DEBUG=true

# Server management
racerctl server start    # Start backend
racerctl server stop     # Stop backend
racerctl server status   # Check status
```

### All Commands

```bash
# User commands (racer)
racer run --project-name "name" --path ./project --app-port 8000
racer validate --path ./project
racer dockerfile --path ./project
racer status --project-name "name"
racer scale --project-name "name" --instances 3 --app-port 8000
racer rerun --project-name "name" --environment DEBUG=true
racer list-projects
racer stop --project-name "name"
racer remove --project-name "name"

# Admin commands (racerctl)
racerctl server start|stop|status|restart
racerctl containers list|stop <id>|remove <id>
racerctl services list|logs <name>|remove <name>
```

## API

The backend provides a RESTful API at `http://localhost:8001`:

- `GET /health` - Health check
- `POST /validate` - Validate conda-project
- `POST /containers/run` - Run container
- `POST /project/scale` - Scale project
- `POST /project/rerun` - Rerun project
- `GET /containers` - List containers

## Port Management

Simple port management with automatic load balancing:

```bash
# Your app exposes port 8000 - we handle the rest!
racer run --project-name "my-app" --path ./project --app-port 8000

# Scale with automatic load balancing
racer scale --project-name "my-app" --instances 3 --app-port 8000
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
make shell              # Start interactive shell with environment activated
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
racer run --project-name "my-app" --path ./my-project --app-port 8000

# Check status
racer status --project-name "my-app"

# Scale up
racer scale --project-name "my-app" --instances 3 --app-port 8000

# Restart with new config
racer rerun --project-name "my-app" --environment DEBUG=true
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
racer list-projects
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `make test`
5. Submit a pull request

## License

This project is licensed under the MIT License.
