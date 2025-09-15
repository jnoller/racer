"""
Integration tests for CLI commands.
"""

import pytest
import tempfile
import subprocess
import time
import os
from pathlib import Path
from unittest.mock import patch, Mock


class TestCLICommands:
    """Test cases for CLI command functionality."""
    
    def test_racer_run_command_help(self):
        """Test racer run command help."""
        result = subprocess.run(
            ["racer", "run", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Run a conda-project by building and running a Docker container" in result.stdout
        assert "--project-name" in result.stdout
        assert "--path" in result.stdout
    
    def test_racer_status_command_help(self):
        """Test racer status command help."""
        result = subprocess.run(
            ["racer", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the status of a running project" in result.stdout
        assert "--project-name" in result.stdout
        assert "--container-id" in result.stdout
    
    def test_racer_rerun_command_help(self):
        """Test racer rerun command help."""
        result = subprocess.run(
            ["racer", "rerun", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Rerun a project by stopping the existing container" in result.stdout
        assert "--project-name" in result.stdout
        assert "--no-rebuild" in result.stdout
    
    def test_racer_scale_command_help(self):
        """Test racer scale command help."""
        result = subprocess.run(
            ["racer", "scale", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Scale a project to run multiple instances" in result.stdout
        assert "--project-name" in result.stdout
        assert "--instances" in result.stdout
    
    def test_racerctl_help(self):
        """Test racerctl help command."""
        result = subprocess.run(
            ["racerctl", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "RacerCTL - Admin CLI for the Racer deployment system" in result.stdout
        assert "containers" in result.stdout
        assert "health" in result.stdout
    
    def test_racerctl_containers_help(self):
        """Test racerctl containers help."""
        result = subprocess.run(
            ["racerctl", "containers", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Manage Docker containers" in result.stdout
        assert "list" in result.stdout
        assert "stop" in result.stdout
    
    def test_racerctl_health_help(self):
        """Test racerctl health help."""
        result = subprocess.run(
            ["racerctl", "health", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the health status of the Racer API server" in result.stdout
    
    @pytest.mark.integration
    def test_racer_run_with_mock_api(self):
        """Test racer run command with mocked API."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "test-project"
            project_dir.mkdir()
            
            # Create basic conda-project.yml
            conda_project_yml = project_dir / "conda-project.yml"
            conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
commands:
  default: python main.py
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
            
            # Create main.py
            main_py = project_dir / "main.py"
            main_py.write_text("print('Hello from test project')")
            
            # Mock the API client
            with patch('src.client.api.RacerAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                # Mock successful API response
                mock_client.run_container.return_value = {
                    "success": True,
                    "container_id": "test-container-123",
                    "container_name": "test-project-123",
                    "status": "running",
                    "ports": {"8000/tcp": 8000},
                    "message": "Container started successfully"
                }
                
                # Run the command
                result = subprocess.run(
                    ["racer", "run", "--project-name", "test-project", "--path", str(project_dir)],
                    capture_output=True,
                    text=True
                )
                
                # Verify the command succeeded
                assert result.returncode == 0
                assert "Container started successfully" in result.stdout
                assert "test-container-123" in result.stdout
    
    @pytest.mark.integration
    def test_racer_status_with_mock_api(self):
        """Test racer status command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_project_status.return_value = {
                "success": True,
                "container_id": "test-container-123",
                "container_name": "test-project-123",
                "status": "running",
                "ports": {"8000/tcp": 8000},
                "started_at": "2023-01-01T00:00:00",
                "image": "test-project:latest"
            }
            
            # Run the command
            result = subprocess.run(
                ["racer", "status", "--container-id", "test-container-123"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "test-container-123" in result.stdout
            assert "running" in result.stdout
    
    @pytest.mark.integration
    def test_racer_rerun_with_mock_api(self):
        """Test racer rerun command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.rerun_project.return_value = {
                "success": True,
                "old_container_id": "old-container-123",
                "new_container_id": "new-container-456",
                "container_name": "test-project-456",
                "status": "running",
                "ports": {"8000/tcp": 8000},
                "message": "Project rerun successful"
            }
            
            # Run the command
            result = subprocess.run(
                ["racer", "rerun", "--project-id", "test-project-123"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Project rerun successful" in result.stdout
            assert "new-container-456" in result.stdout
    
    @pytest.mark.integration
    def test_racer_scale_with_mock_api(self):
        """Test racer scale command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.scale_project.return_value = {
                "success": True,
                "project_name": "test-project",
                "instances": 3,
                "containers": [
                    {"id": "container-1", "name": "test-project_1"},
                    {"id": "container-2", "name": "test-project_2"},
                    {"id": "container-3", "name": "test-project_3"}
                ],
                "message": "Project scaling successful"
            }
            
            # Run the command
            result = subprocess.run(
                ["racer", "scale", "--project-name", "test-project", "--instances", "3"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Project scaling successful" in result.stdout
            assert "3 instance(s)" in result.stdout
