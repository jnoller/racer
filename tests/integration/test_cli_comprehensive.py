"""
Comprehensive CLI command tests covering all README commands.
"""

import pytest
import tempfile
import subprocess
import time
import os
from pathlib import Path
from unittest.mock import patch, Mock


class TestRacerCLICommands:
    """Test cases for all racer CLI commands from README."""
    
    def test_racer_dockerfile_command_help(self):
        """Test racer dockerfile command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "dockerfile", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Generate a Dockerfile for a conda-project" in result.stdout
        assert "--path" in result.stdout
        assert "--custom-commands" in result.stdout
    
    def test_racer_dockerfile_command_with_mock_api(self):
        """Test racer dockerfile command with mocked API."""
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
            
            # Mock the API client
            with patch('src.client.api.RacerAPIClient') as mock_client_class:
                mock_client = Mock()
                mock_client_class.return_value = mock_client
                
                # Mock successful API response
                mock_client.generate_dockerfile.return_value = {
                    "success": True,
                    "dockerfile_content": "FROM continuumio/miniconda3\n# Test Dockerfile",
                    "message": "Dockerfile generated successfully"
                }
                
                # Run the command
                result = subprocess.run(
                    ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                     "dockerfile", "--path", str(project_dir)],
                    capture_output=True,
                    text=True
                )
                
                # Verify the command succeeded
                assert result.returncode == 0
                assert "Dockerfile generated successfully" in result.stdout
    
    def test_racer_list_projects_command_help(self):
        """Test racer list-projects command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "list-projects", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "List all running projects" in result.stdout
        assert "--verbose" in result.stdout
    
    def test_racer_list_projects_command_with_mock_api(self):
        """Test racer list-projects command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.list_projects.return_value = {
                "success": True,
                "projects": [
                    {
                        "project_id": "test-1",
                        "project_name": "test-project",
                        "status": "running",
                        "ports": {"8000/tcp": 8000}
                    }
                ],
                "count": 1
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "list-projects"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "test-project" in result.stdout
            assert "running" in result.stdout
    
    def test_racer_scale_up_command_help(self):
        """Test racer scale-up command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "scale-up", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Scale up an existing project to more instances" in result.stdout
        assert "--project-name" in result.stdout
        assert "--instances" in result.stdout
    
    def test_racer_scale_up_command_with_mock_api(self):
        """Test racer scale-up command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.scale_up_project.return_value = {
                "success": True,
                "project_name": "test-project",
                "instances": 5,
                "message": "Project scaled up successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "scale-up", "--project-name", "test-project", "--instances", "5"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Project scaled up successfully" in result.stdout
    
    def test_racer_scale_down_command_help(self):
        """Test racer scale-down command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "scale-down", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Scale down an existing project to fewer instances" in result.stdout
        assert "--project-name" in result.stdout
        assert "--instances" in result.stdout
    
    def test_racer_scale_down_command_with_mock_api(self):
        """Test racer scale-down command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.scale_down_project.return_value = {
                "success": True,
                "project_name": "test-project",
                "instances": 2,
                "message": "Project scaled down successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "scale-down", "--project-name", "test-project", "--instances", "2"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Project scaled down successfully" in result.stdout
    
    def test_racer_swarm_status_command_help(self):
        """Test racer swarm-status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "swarm-status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the status of Docker Swarm services" in result.stdout
        assert "--project-name" in result.stdout
    
    def test_racer_swarm_status_command_with_mock_api(self):
        """Test racer swarm-status command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_swarm_service_status.return_value = {
                "success": True,
                "service_name": "test-project",
                "status": "running",
                "replicas": 3,
                "message": "Service status retrieved successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "swarm-status", "--project-name", "test-project"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Service status retrieved successfully" in result.stdout
    
    def test_racer_swarm_logs_command_help(self):
        """Test racer swarm-logs command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "swarm-logs", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Get logs from a Docker Swarm service" in result.stdout
        assert "--project-name" in result.stdout
        assert "--tail" in result.stdout
    
    def test_racer_swarm_logs_command_with_mock_api(self):
        """Test racer swarm-logs command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_swarm_service_logs.return_value = {
                "success": True,
                "service_name": "test-project",
                "logs": "Service log line 1\nService log line 2",
                "message": "Service logs retrieved successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "swarm-logs", "--project-name", "test-project"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Service logs retrieved successfully" in result.stdout
    
    def test_racer_swarm_remove_command_help(self):
        """Test racer swarm-remove command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "swarm-remove", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Remove a Docker Swarm service" in result.stdout
        assert "--project-name" in result.stdout
        assert "--force" in result.stdout
    
    def test_racer_swarm_remove_command_with_mock_api(self):
        """Test racer swarm-remove command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.remove_swarm_service.return_value = {
                "success": True,
                "service_name": "test-project",
                "message": "Service removed successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "swarm-remove", "--project-name", "test-project"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Service removed successfully" in result.stdout
    
    def test_racer_rerun_command_updated_interface(self):
        """Test racer rerun command with updated project-name only interface."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.rerun_project.return_value = {
                "success": True,
                "old_container_id": "old-container-123",
                "new_container_id": "new-container-456",
                "message": "Project rerun successful"
            }
            
            # Run the command with project-name (new interface)
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "rerun", "--project-name", "test-project"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Project rerun successful" in result.stdout
    
    def test_racer_status_different_identification_methods(self):
        """Test racer status command with different identification methods."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_project_status.return_value = {
                "success": True,
                "container_id": "test-container-123",
                "project_name": "test-project",
                "status": "running",
                "ports": {"8000/tcp": 8000}
            }
            
            # Test with project-name
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "status", "--project-name", "test-project"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "test-container-123" in result.stdout
            
            # Test with project-id
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "status", "--project-id", "test-project-123"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "test-container-123" in result.stdout
            
            # Test with container-id
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "status", "--container-id", "test-container-123"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0
            assert "test-container-123" in result.stdout


class TestRacerctlCLICommands:
    """Test cases for all racerctl CLI commands from README."""
    
    def test_racerctl_info_command_help(self):
        """Test racerctl info command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "info", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Get basic information about the Racer API server" in result.stdout
    
    def test_racerctl_info_command_with_mock_api(self):
        """Test racerctl info command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_info.return_value = {
                "success": True,
                "service": "Racer API",
                "version": "0.1.0",
                "uptime": "1h 30m",
                "message": "API information retrieved successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "info"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "API information retrieved successfully" in result.stdout
    
    def test_racerctl_server_start_command_help(self):
        """Test racerctl server start command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "server", "start", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Start the Racer backend server" in result.stdout
        assert "--port" in result.stdout
        assert "--foreground" in result.stdout
    
    def test_racerctl_server_stop_command_help(self):
        """Test racerctl server stop command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "server", "stop", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Stop the Racer backend server" in result.stdout
        assert "--port" in result.stdout
        assert "--force" in result.stdout
    
    def test_racerctl_server_status_command_help(self):
        """Test racerctl server status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "server", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the status of the Racer backend server" in result.stdout
        assert "--port" in result.stdout
    
    def test_racerctl_server_restart_command_help(self):
        """Test racerctl server restart command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "server", "restart", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Restart the Racer backend server" in result.stdout
        assert "--port" in result.stdout
        assert "--foreground" in result.stdout
    
    def test_racerctl_containers_status_command_help(self):
        """Test racerctl containers status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Get the status of a specific container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
    
    def test_racerctl_containers_status_command_with_mock_api(self):
        """Test racerctl containers status command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_container_status.return_value = {
                "success": True,
                "container_id": "test-container-123",
                "status": "running",
                "ports": {"8000/tcp": 8000},
                "message": "Container status retrieved successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", 
                 "containers", "status", "test-container-123"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Container status retrieved successfully" in result.stdout
    
    def test_racerctl_containers_logs_command_help(self):
        """Test racerctl containers logs command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "logs", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Get logs from a specific container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
        assert "--tail" in result.stdout
    
    def test_racerctl_containers_logs_command_with_mock_api(self):
        """Test racerctl containers logs command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.get_container_logs.return_value = {
                "success": True,
                "container_id": "test-container-123",
                "logs": "Container log line 1\nContainer log line 2",
                "message": "Container logs retrieved successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", 
                 "containers", "logs", "test-container-123"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Container logs retrieved successfully" in result.stdout
    
    def test_racerctl_containers_stop_command_help(self):
        """Test racerctl containers stop command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "stop", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Stop a running container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
    
    def test_racerctl_containers_stop_command_with_mock_api(self):
        """Test racerctl containers stop command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.stop_container.return_value = {
                "success": True,
                "container_id": "test-container-123",
                "message": "Container stopped successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", 
                 "containers", "stop", "test-container-123"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Container stopped successfully" in result.stdout
    
    def test_racerctl_containers_remove_command_help(self):
        """Test racerctl containers remove command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "remove", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Remove a container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
    
    def test_racerctl_containers_remove_command_with_mock_api(self):
        """Test racerctl containers remove command with mocked API."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.remove_container.return_value = {
                "success": True,
                "container_id": "test-container-123",
                "message": "Container removed successfully"
            }
            
            # Run the command
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", 
                 "containers", "remove", "test-container-123"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Container removed successfully" in result.stdout


class TestAdvancedFunctionality:
    """Test cases for advanced functionality like port mapping, environment variables, etc."""
    
    def test_racer_run_with_port_mapping(self):
        """Test racer run command with port mapping."""
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
                    "ports": {"8080/tcp": 8080},
                    "message": "Container started successfully"
                }
                
                # Run the command with port mapping
                result = subprocess.run(
                    ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                     "run", "--project-name", "test-project", "--path", str(project_dir), 
                     "--ports", "8080:8000"],
                    capture_output=True,
                    text=True
                )
                
                # Verify the command succeeded
                assert result.returncode == 0
                assert "Container started successfully" in result.stdout
                assert "8080" in result.stdout
    
    def test_racer_run_with_environment_variables(self):
        """Test racer run command with environment variables."""
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
                    "environment": {"DEBUG": "true", "PORT": "8000"},
                    "message": "Container started successfully"
                }
                
                # Run the command with environment variables
                result = subprocess.run(
                    ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                     "run", "--project-name", "test-project", "--path", str(project_dir), 
                     "--env", "DEBUG=true,PORT=8000"],
                    capture_output=True,
                    text=True
                )
                
                # Verify the command succeeded
                assert result.returncode == 0
                assert "Container started successfully" in result.stdout
    
    def test_racer_run_with_custom_commands(self):
        """Test racer run command with custom commands."""
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
                    "custom_commands": ["apt-get update", "apt-get install -y curl"],
                    "message": "Container started successfully"
                }
                
                # Run the command with custom commands
                result = subprocess.run(
                    ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                     "run", "--project-name", "test-project", "--path", str(project_dir), 
                     "--custom-commands", "apt-get update,apt-get install -y curl"],
                    capture_output=True,
                    text=True
                )
                
                # Verify the command succeeded
                assert result.returncode == 0
                assert "Container started successfully" in result.stdout
    
    def test_racer_scale_with_git_repository(self):
        """Test racer scale command with git repository."""
        with patch('src.client.api.RacerAPIClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock successful API response
            mock_client.scale_project.return_value = {
                "success": True,
                "project_name": "test-project",
                "instances": 3,
                "git_url": "https://github.com/user/repo.git",
                "message": "Project scaled successfully"
            }
            
            # Run the command with git repository
            result = subprocess.run(
                ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", 
                 "scale", "--project-name", "test-project", "--instances", "3", 
                 "--git", "https://github.com/user/repo.git"],
                capture_output=True,
                text=True
            )
            
            # Verify the command succeeded
            assert result.returncode == 0
            assert "Project scaled successfully" in result.stdout
