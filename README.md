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
racer run --project-name "my-app" --path /path/to/your/conda-project
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

### User Commands (`racer`)

#### Deploy and Run Projects

```bash
# Deploy a local project
racer run --project-name "my-app" --path ./my-project --app-port 8000

# Deploy from Git repository
racer run --project-name "my-app" --git https://github.com/user/repo.git --app-port 8000

# Deploy with custom environment variables
racer run --project-name "my-app" --path ./my-project --app-port 8000 \
  --environment DEBUG=true,API_KEY=secret123

# Deploy with custom command
racer run --project-name "my-app" --path ./my-project --app-port 8000 \
  --command "python app.py --port 8000"

# Deploy with custom build commands
racer run --project-name "my-app" --path ./my-project --app-port 8000 \
  --custom-commands "pip install -r requirements.txt,apt-get update"
```

#### Scale Projects

```bash
# Scale to multiple instances (creates Docker Swarm service)
racer scale --project-name "my-app" --instances 3 --app-port 8000

# Scale from local project
racer scale --project-name "my-app" --instances 5 --path ./my-project --app-port 8000

# Scale from Git repository
racer scale --project-name "my-app" --instances 3 --git https://github.com/user/repo.git --app-port 8000

# Scale with custom configuration
racer scale --project-name "my-app" --instances 2 --path ./my-project --app-port 8000 \
  --environment DEBUG=true --command "python app.py"
```

#### Dynamic Scaling

```bash
# Scale a project to multiple instances
racer scale --project-name "my-app" --instances 5 --path ./my-project --app-port 8000

# Scale down by running scale with fewer instances
racer scale --project-name "my-app" --instances 2 --path ./my-project --app-port 8000
```

#### Rerun Projects

```bash
# Rerun with rebuilt image (includes source changes)
racer rerun --project-name "my-app"

# Fast restart without rebuilding (configuration changes only)
racer rerun --project-name "my-app" --no-rebuild

# Rerun with new environment variables
racer rerun --project-name "my-app" --environment DEBUG=true,LOG_LEVEL=debug

# Rerun with new command
racer rerun --project-name "my-app" --command "python app.py --debug"

# Rerun with custom build commands
racer rerun --project-name "my-app" --custom-commands "pip install -r requirements.txt"

# List projects before rerunning
racer rerun --list
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

# Generate Dockerfile
racer dockerfile --path ./my-project

# Generate Dockerfile with custom commands
racer dockerfile --path ./my-project --custom-commands "pip install -r requirements.txt"
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
