"""
Basic tests for Racer functionality.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.backend.dockerfile_template import generate_dockerfile
from src.backend.project_validator import validate_conda_project


def test_dockerfile_generation():
    """Test basic Dockerfile generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "test-project"
        project_dir.mkdir()
        
        # Create basic conda-project.yml
        conda_project_yml = project_dir / "conda-project.yml"
        conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
""")
        
        # Create environment.yml
        environment_yml = project_dir / "environment.yml"
        environment_yml.write_text("""name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
variables: {}
""")
        
        # Test Dockerfile generation
        result = generate_dockerfile(str(project_dir))
        
        assert "FROM continuumio/miniconda3" in result
        assert "conda install conda-forge::conda-project" in result
        assert "COPY . /project" in result
        assert 'conda project install --force' in result


def test_dockerfile_generation_with_custom_commands():
    """Test Dockerfile generation with custom commands."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "test-project"
        project_dir.mkdir()
        
        # Create basic conda-project.yml
        conda_project_yml = project_dir / "conda-project.yml"
        conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
""")
        
        # Create environment.yml
        environment_yml = project_dir / "environment.yml"
        environment_yml.write_text("""name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
variables: {}
""")
        
        # Test Dockerfile generation with custom commands
        custom_commands = ["apt-get update", "apt-get install -y curl"]
        result = generate_dockerfile(str(project_dir), custom_commands)
        
        assert "FROM continuumio/miniconda3" in result
        # Note: Custom commands are not currently implemented in the template
        # This test verifies the function doesn't crash with custom commands


def test_project_validation():
    """Test basic project validation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / "test-project"
        project_dir.mkdir()
        
        # Create basic conda-project.yml
        conda_project_yml = project_dir / "conda-project.yml"
        conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
""")
        
        # Create environment.yml
        environment_yml = project_dir / "environment.yml"
        environment_yml.write_text("""name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
variables: {}
""")
        
        # Test project validation
        result = validate_conda_project(str(project_dir))
        
        assert result["valid"] is True
        assert result["project_name"] == "test-project"
        assert "default" in result["environments"]


def test_project_validation_missing_files():
    """Test project validation with missing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test with empty directory
        try:
            result = validate_conda_project(temp_dir)
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "conda-project.yml" in str(e)


def test_cli_imports():
    """Test that CLI modules can be imported."""
    from src.client.racer_cli import cli as racer_cli
    from src.client.racerctl import cli as racerctl_cli
    
    assert racer_cli is not None
    assert racerctl_cli is not None


def test_api_client_import():
    """Test that API client can be imported."""
    from src.client.api import RacerAPIClient, RacerAPIError
    
    assert RacerAPIClient is not None
    assert RacerAPIError is not None


def test_docker_manager_import():
    """Test that Docker manager can be imported."""
    from src.backend.docker_manager import ContainerManager
    
    assert ContainerManager is not None


def test_backend_imports():
    """Test that backend modules can be imported."""
    from src.backend.project_validator import validate_conda_project
    from src.backend.dockerfile_template import generate_dockerfile
    from src.backend.docker_manager import ContainerManager
    
    assert validate_conda_project is not None
    assert generate_dockerfile is not None
    assert ContainerManager is not None
