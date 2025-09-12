"""
Unit tests for CLI commands.
"""

import pytest
from unittest.mock import Mock, patch
from click.testing import CliRunner
from src.client.racer_cli import cli as racer_cli
from src.client.racerctl import cli as racerctl_cli


class TestRacerCLI:
    """Test cases for racer CLI commands."""
    
    def test_racer_cli_help(self):
        """Test racer CLI help command."""
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Racer - Rapid deployment system for conda-projects" in result.output
        assert "run" in result.output
        assert "validate" in result.output
        assert "dockerfile" in result.output
        assert "status" in result.output
    
    def test_racer_cli_version(self):
        """Test racer CLI version."""
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['--help'])
        
        assert result.exit_code == 0
        assert "Options:" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_status_success(self, mock_client_class):
        """Test racer status command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.side_effect = [
            {"status": "healthy", "timestamp": "2023-01-01T00:00:00"},
            {"message": "Racer API Server", "version": "0.1.0", "uptime": "1h"}
        ]
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['status'])
        
        assert result.exit_code == 0
        assert "✓ Racer API is healthy" in result.output
        assert "Version: 0.1.0" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_status_failure(self, mock_client_class):
        """Test racer status command failure."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.side_effect = Exception("Connection failed")
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['status'])
        
        assert result.exit_code == 1
        assert "Unexpected error: Connection failed" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_validate_success(self, mock_client_class):
        """Test racer validate command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "valid": True,
            "project_name": "test-project",
            "project_version": "1.0.0",
            "environments": ["default"],
            "channels": ["conda-forge"],
            "warnings": [],
            "errors": []
        }
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['validate', '--path', '/test/path'])
        
        assert result.exit_code == 0
        assert "✓ Project is valid" in result.output
        assert "Project: test-project" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_validate_failure(self, mock_client_class):
        """Test racer validate command failure."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "valid": False,
            "project_name": "test-project",
            "project_version": None,
            "environments": [],
            "channels": [],
            "warnings": [],
            "errors": ["conda-project.yml not found"]
        }
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['validate', '--path', '/test/path'])
        
        assert result.exit_code == 0
        assert "✗ Project is invalid" in result.output
        assert "✗ conda-project.yml not found" in result.output
    
    def test_racer_validate_missing_path(self):
        """Test racer validate command with missing path."""
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['validate'])
        
        assert result.exit_code == 1
        assert "Either --path or --git must be specified" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_dockerfile_success(self, mock_client_class):
        """Test racer dockerfile command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "project_name": "test-project",
            "dockerfile_path": "/test/path/Dockerfile",
            "dockerfile_content": "FROM continuumio/miniconda3"
        }
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['dockerfile', '--path', '/test/path'])
        
        assert result.exit_code == 0
        assert "✓ Dockerfile generated successfully" in result.output
        assert "Project: test-project" in result.output
        assert "FROM continuumio/miniconda3" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_run_success(self, mock_client_class):
        """Test racer run command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "container_id": "test-container-id",
            "container_name": "test-container",
            "ports": {"8000/tcp": 8080},
            "status": "running",
            "message": "Container started successfully"
        }
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, [
            'run', '--path', '/test/path', '--ports', '8080:8000'
        ])
        
        assert result.exit_code == 0
        assert "✓ Container started successfully" in result.output
        assert "Container ID: test-container-id" in result.output
        assert "8080 -> 8000/tcp" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racer_run_build_only(self, mock_client_class):
        """Test racer run command with build-only flag."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "project_name": "test-project",
            "dockerfile_path": "/test/path/Dockerfile",
            "instructions": {
                "build": "docker build -t test-project /test/path"
            }
        }
        
        runner = CliRunner()
        result = runner.invoke(racer_cli, [
            'run', '--path', '/test/path', '--build-only'
        ])
        
        assert result.exit_code == 0
        assert "✓ Project prepared for building" in result.output
        assert "Project: test-project" in result.output
    
    def test_racer_run_missing_path(self):
        """Test racer run command with missing path."""
        runner = CliRunner()
        result = runner.invoke(racer_cli, ['run'])
        
        assert result.exit_code == 1
        assert "Either --path or --git must be specified" in result.output


class TestRacerCTLCLI:
    """Test cases for racerctl CLI commands."""
    
    def test_racerctl_cli_help(self):
        """Test racerctl CLI help command."""
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['--help'])
        
        assert result.exit_code == 0
        assert "RacerCTL - Admin CLI for the Racer deployment system" in result.output
        assert "containers" in result.output
        assert "health" in result.output
        assert "liveness" in result.output
        assert "readiness" in result.output
        assert "info" in result.output
    
    def test_racerctl_cli_version(self):
        """Test racerctl CLI version."""
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['--version'])
        
        assert result.exit_code == 0
        assert "0.1.0" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_health_success(self, mock_client_class):
        """Test racerctl health command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.health.return_value = {
            "status": "healthy",
            "timestamp": "2023-01-01T00:00:00",
            "version": "0.1.0",
            "service": "racer-api"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['health'])
        
        assert result.exit_code == 0
        assert "✓ racer-api v0.1.0 is healthy" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_liveness_success(self, mock_client_class):
        """Test racerctl liveness command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.liveness.return_value = {
            "alive": True,
            "uptime": "1h 30m",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['liveness'])
        
        assert result.exit_code == 0
        assert "✓ Server is alive" in result.output
        assert "Uptime: 1h 30m" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_readiness_success(self, mock_client_class):
        """Test racerctl readiness command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.readiness.return_value = {
            "ready": True,
            "checks": {
                "docker": "ok",
                "database": "ok"
            },
            "timestamp": "2023-01-01T00:00:00"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['readiness'])
        
        assert result.exit_code == 0
        assert "✓ Server is ready" in result.output
        assert "✓ docker: ok" in result.output
        assert "✓ database: ok" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_info_success(self, mock_client_class):
        """Test racerctl info command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.info.return_value = {
            "message": "Racer API Server",
            "version": "0.1.0",
            "health": "/health",
            "docs": "/docs"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['info'])
        
        assert result.exit_code == 0
        assert "Racer API Server v0.1.0" in result.output
        assert "Available endpoints:" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_list_success(self, mock_client_class):
        """Test racerctl containers list command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "containers": [
                {
                    "container_id": "test-id",
                    "container_name": "test-container",
                    "project_name": "test-project",
                    "status": "running",
                    "image": "test-image:latest",
                    "started_at": "2023-01-01T00:00:00",
                    "ports": {"8000/tcp": 8080}
                }
            ],
            "count": 1
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'list'])
        
        assert result.exit_code == 0
        assert "Found 1 container(s):" in result.output
        assert "• test-container" in result.output
        assert "ID: test-id" in result.output
        assert "8080 -> 8000/tcp" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_list_empty(self, mock_client_class):
        """Test racerctl containers list command with no containers."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "containers": [],
            "count": 0
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'list'])
        
        assert result.exit_code == 0
        assert "No containers found." in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_status_success(self, mock_client_class):
        """Test racerctl containers status command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "container_id": "test-id",
            "container_name": "test-container",
            "status": "running",
            "image": "test-image:latest",
            "started_at": "2023-01-01T00:00:00",
            "ports": {"8000/tcp": 8080}
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'status', 'test-id'])
        
        assert result.exit_code == 0
        assert "✓ Container Status" in result.output
        assert "Name: test-container" in result.output
        assert "Status: running" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_logs_success(self, mock_client_class):
        """Test racerctl containers logs command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "container_id": "test-id",
            "logs": "Test log output\nAnother log line"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'logs', 'test-id'])
        
        assert result.exit_code == 0
        assert "Logs for container test-id:" in result.output
        assert "Test log output" in result.output
        assert "Another log line" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_stop_success(self, mock_client_class):
        """Test racerctl containers stop command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "container_id": "test-id",
            "message": "Container stopped successfully"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'stop', 'test-id'])
        
        assert result.exit_code == 0
        assert "✓ Container stopped successfully" in result.output
        assert "Container ID: test-id" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_remove_success(self, mock_client_class):
        """Test racerctl containers remove command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "container_id": "test-id",
            "message": "Container removed successfully"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'remove', 'test-id'])
        
        assert result.exit_code == 0
        assert "✓ Container removed successfully" in result.output
        assert "Container ID: test-id" in result.output
    
    @patch('src.client.api.RacerAPIClient')
    def test_racerctl_containers_cleanup_success(self, mock_client_class):
        """Test racerctl containers cleanup command success."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client._make_request.return_value = {
            "success": True,
            "cleaned_up": 2,
            "message": "Cleaned up 2 stopped containers"
        }
        
        runner = CliRunner()
        result = runner.invoke(racerctl_cli, ['containers', 'cleanup'])
        
        assert result.exit_code == 0
        assert "✓ Cleanup completed" in result.output
        assert "Removed 2 stopped container(s)" in result.output
