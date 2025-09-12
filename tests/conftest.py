"""
Shared test fixtures and configuration.
"""

import pytest
import tempfile
import shutil
import os
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch
import requests


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_project_dir(temp_dir):
    """Create a test conda-project directory."""
    project_dir = Path(temp_dir) / "test-project"
    project_dir.mkdir()
    
    # Create conda-project.yml
    conda_project_yml = project_dir / "conda-project.yml"
    conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
commands:
  run:
    cmd: python main.py
    environment: default
""")
    
    # Create environment.yml
    environment_yml = project_dir / "environment.yml"
    environment_yml.write_text("""name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
  - fastapi
  - uvicorn
  - requests
variables: {}
platforms:
  - osx-64
  - win-64
  - osx-arm64
  - linux-64
  - linux-aarch64
""")
    
    # Create main.py
    main_py = project_dir / "main.py"
    main_py.write_text("""import os
import sys
import platform
from fastapi import FastAPI

app = FastAPI(title="Test Project API")

@app.get("/")
async def root():
    return {"message": "Hello from test-project API!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "test-project"}

if __name__ == "__main__":
    print(f"Hello from test-project!")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
""")
    
    return str(project_dir)


@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing."""
    with patch('src.backend.docker_manager.docker.from_env') as mock_from_env:
        mock_client = Mock()
        mock_from_env.return_value = mock_client
        mock_client.ping.return_value = True
        
        # Mock image building
        mock_image = Mock()
        mock_image.id = "test-image-id"
        mock_image.tags = ["test-image:latest"]
        mock_client.images.build.return_value = (mock_image, [])
        
        # Mock container running
        mock_container = Mock()
        mock_container.id = "test-container-id"
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.image.tags = ["test-image:latest"]
        mock_container.image.id = "test-image-id"
        mock_container.logs.return_value = b"Test log output"
        mock_client.containers.run.return_value = mock_container
        
        yield mock_client


@pytest.fixture
def api_server():
    """Start API server for integration tests."""
    # Start the server in background
    process = subprocess.Popen([
        "conda", "run", "-n", "racer", "python", "-m", "uvicorn", 
        "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"
    ], cwd=os.getcwd())
    
    # Wait for server to start
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            time.sleep(1)
    else:
        process.terminate()
        pytest.skip("Could not start API server")
    
    yield "http://localhost:8000"
    
    # Cleanup
    process.terminate()
    process.wait()


@pytest.fixture
def sample_dockerfile():
    """Sample Dockerfile content for testing."""
    return """FROM continuumio/miniconda3 as miniconda
### Install and configure miniconda
RUN conda install conda-forge::conda-project --yes && conda clean --all --yes

FROM miniconda as conda-project

COPY --from=miniconda /opt/conda /opt/conda

### Set timezone
ENV TZ=US/Central
RUN cp /usr/share/zoneinfo/${TZ} /etc/localtime \\
    && echo ${TZ} > /etc/timezone

ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

ENV PATH=/opt/conda/bin:$PATH
ENV HOME=/project

COPY . /project
RUN chown -R 1001:1001 /project

USER 1001
WORKDIR /project
RUN ["conda", "project", "prepare", "--force"]

ENTRYPOINT ["conda", "project", "run"]
CMD []
"""


@pytest.fixture
def sample_conda_project_yml():
    """Sample conda-project.yml content for testing."""
    return """name: test-project
environments:
  default:
    - environment.yml
variables: {}
commands:
  run:
    cmd: python main.py
    environment: default
"""


@pytest.fixture
def sample_environment_yml():
    """Sample environment.yml content for testing."""
    return """name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
  - fastapi
  - uvicorn
  - requests
variables: {}
platforms:
  - osx-64
  - win-64
  - osx-arm64
  - linux-64
  - linux-aarch64
"""
