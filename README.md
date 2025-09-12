# `racer` - Rapid deployment system for conda-projects

## Summary

`racer` is a comprehensive deployment platform that simplifies the process of deploying conda-based applications to containerized environments. The system consists of:

1. **Backend Orchestration API** (FastAPI) - A Heroku/Fly.io-like REST API server that deploys `conda-project` based applications to one or more Docker containers and manages them on behalf of the user
2. **Command Line Client** (`racerctl`) - User-facing commands such as `racerctl init`, `racerctl deploy`, and more

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

# Activate the environment
conda activate racer
```

### 3. Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create environment with Python 3.11 (recommended)
conda create -n racer python=3.11 -y

# Activate the environment
conda activate racer

# Install conda-project (required for conda project management)
conda install -c conda-forge conda-project -y

# Install all Python dependencies via pip
pip install -r requirements.txt
```

### 4. Development Setup

#### Using Makefile (Recommended)

```bash
# Install development dependencies and client
make install-dev

# Run backend server
make backend

# Install client in development mode
make client
```

#### Manual Development Setup

```bash
# Install development dependencies (if separate from main requirements)
pip install -r requirements-dev.txt

# Backend Development
cd src/backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Client Development
cd src/client
pip install -e .
racerctl --help
```

## Project Structure

```
racer/
├── README.md
├── Makefile              # Development automation
├── requirements.txt       # Main Python dependencies
├── requirements-dev.txt   # Development dependencies (optional)
├── src/
│   ├── backend/           # FastAPI orchestration server
│   │   └── main.py       # FastAPI application entry point
│   └── client/           # Command line client (racerctl)
│       ├── __init__.py
│       ├── cli.py        # CLI command definitions
│       └── setup.py
└── docs/                 # Additional documentation
```

## Makefile Commands

The project includes a Makefile for common development tasks:

```bash
# Show all available commands
make help

# Setup conda environment and install dependencies
make setup

# Install development dependencies
make install-dev

# Run backend server
make backend

# Install client in development mode
make client

# Run tests
make test

# Run linting
make lint

# Format code
make format

# Clean up conda environment
make clean
```

## Environment Management

### Using Conda Environments

We recommend using conda environments for dependency management:

```bash
# List all environments
conda env list

# Activate the racer environment
conda activate racer

# Deactivate the environment
conda deactivate

# Remove the environment (if needed)
conda env remove -n racer
```

### Dependency Management

- **Main Dependencies**: Uses `pip` for Python package management with top-level `requirements.txt`
- **Development Dependencies**: Optional `requirements-dev.txt` for development tools
- **Conda Projects**: Uses `conda-project` for conda environment management
- **Client**: Uses `pip` with `setup.py` for development installation

## Configuration

### Backend Configuration

Create a `.env` file in the `src/backend` directory:

```bash
# Database configuration
DATABASE_URL=sqlite:///./racer.db

# Docker configuration
DOCKER_HOST=unix:///var/run/docker.sock

# API configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=True
```

### Client Configuration

The client can be configured via environment variables or a config file:

```bash
# Set the backend API URL
export RACER_API_URL=http://localhost:8000

# Or create ~/.racer/config.yaml
api_url: http://localhost:8000
```

## Usage Examples

### Initialize a New Project

```bash
# Initialize a new conda project
racerctl init my-app

# Navigate to the project
cd my-app

# Add dependencies
conda add python=3.11
conda add fastapi uvicorn
```

### Deploy Your Application

```bash
# Deploy to the racer platform
racerctl deploy

# Check deployment status
racerctl status

# View logs
racerctl logs
```

## Troubleshooting

### Common Issues

1. **Conda not found**: Ensure conda is installed and in your PATH
2. **Docker not running**: Start Docker Desktop or Docker daemon
3. **Port conflicts**: Change the API port in the backend configuration
4. **Permission issues**: Ensure your user has Docker permissions

### Getting Help

- Check the logs: `racerctl logs --follow`
- Verify environment: `conda info --envs`
- Test Docker: `docker ps`

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

[Add your license information here]

