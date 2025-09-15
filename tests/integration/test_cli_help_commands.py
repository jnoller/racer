"""
Test CLI help commands to verify all README commands exist and have proper help text.
"""

import pytest
import subprocess


class TestCLIHelpCommands:
    """Test that all CLI commands from README exist and have proper help text."""
    
    def test_racer_help(self):
        """Test racer main help command."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Racer - Rapid deployment system for conda-projects" in result.stdout
        assert "Commands:" in result.stdout
        assert "run" in result.stdout
        assert "validate" in result.stdout
        assert "dockerfile" in result.stdout
        assert "list-projects" in result.stdout
        assert "status" in result.stdout
        assert "scale" in result.stdout
        assert "scale-up" in result.stdout
        assert "scale-down" in result.stdout
        assert "swarm-status" in result.stdout
        assert "swarm-logs" in result.stdout
        assert "swarm-remove" in result.stdout
        assert "rerun" in result.stdout
    
    def test_racer_run_help(self):
        """Test racer run command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "run", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Run a conda-project by building and running a Docker container" in result.stdout
        assert "--project-name" in result.stdout
        assert "--path" in result.stdout
        assert "--git" in result.stdout
        assert "--ports" in result.stdout
        assert "--env" in result.stdout
        assert "--custom-commands" in result.stdout
    
    def test_racer_validate_help(self):
        """Test racer validate command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "validate", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Validate a conda-project directory or git repository" in result.stdout
        assert "--path" in result.stdout
        assert "--git" in result.stdout
    
    def test_racer_dockerfile_help(self):
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
    
    def test_racer_list_projects_help(self):
        """Test racer list-projects command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "list-projects", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "List all running projects" in result.stdout
        assert "--verbose" in result.stdout
    
    def test_racer_status_help(self):
        """Test racer status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the status of a running project or list all projects" in result.stdout
        assert "--project-name" in result.stdout
        assert "--project-id" in result.stdout
        assert "--container-id" in result.stdout
        assert "--list" in result.stdout
    
    def test_racer_scale_help(self):
        """Test racer scale command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "scale", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Scale a project to run multiple instances" in result.stdout
        assert "--project-name" in result.stdout
        assert "--instances" in result.stdout
        assert "--path" in result.stdout
        assert "--git" in result.stdout
        assert "--ports" in result.stdout
    
    def test_racer_scale_up_help(self):
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
    
    def test_racer_scale_down_help(self):
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
    
    def test_racer_swarm_status_help(self):
        """Test racer swarm-status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "swarm-status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the status of Docker Swarm services" in result.stdout
        assert "--project-name" in result.stdout
    
    def test_racer_swarm_logs_help(self):
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
    
    def test_racer_swarm_remove_help(self):
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
    
    def test_racer_rerun_help(self):
        """Test racer rerun command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/racer_cli.py", "rerun", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Rerun a project by stopping the existing container" in result.stdout
        assert "--project-name" in result.stdout
        assert "--no-rebuild" in result.stdout
        assert "--list" in result.stdout
    
    def test_racerctl_help(self):
        """Test racerctl main help command."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "RacerCTL - Admin CLI for the Racer deployment system" in result.stdout
        assert "Commands:" in result.stdout
        assert "health" in result.stdout
        assert "liveness" in result.stdout
        assert "readiness" in result.stdout
        assert "info" in result.stdout
        assert "server" in result.stdout
        assert "containers" in result.stdout
    
    def test_racerctl_health_help(self):
        """Test racerctl health command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "health", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the health status of the Racer API server" in result.stdout
    
    def test_racerctl_liveness_help(self):
        """Test racerctl liveness command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "liveness", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the liveness status of the Racer API server" in result.stdout
    
    def test_racerctl_readiness_help(self):
        """Test racerctl readiness command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "readiness", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the readiness status of the Racer API server" in result.stdout
    
    def test_racerctl_info_help(self):
        """Test racerctl info command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "info", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Get basic information about the Racer API server" in result.stdout
    
    def test_racerctl_server_help(self):
        """Test racerctl server command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "server", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Manage the Racer backend server" in result.stdout
        assert "start" in result.stdout
        assert "stop" in result.stdout
        assert "status" in result.stdout
        assert "restart" in result.stdout
    
    def test_racerctl_server_start_help(self):
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
    
    def test_racerctl_server_stop_help(self):
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
    
    def test_racerctl_server_status_help(self):
        """Test racerctl server status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "server", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Check the status of the Racer backend server" in result.stdout
        assert "--port" in result.stdout
    
    def test_racerctl_server_restart_help(self):
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
    
    def test_racerctl_containers_help(self):
        """Test racerctl containers command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Manage Docker containers" in result.stdout
        assert "list" in result.stdout
        assert "status" in result.stdout
        assert "logs" in result.stdout
        assert "stop" in result.stdout
        assert "remove" in result.stdout
        assert "cleanup" in result.stdout
    
    def test_racerctl_containers_list_help(self):
        """Test racerctl containers list command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "list", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "List all tracked containers" in result.stdout
    
    def test_racerctl_containers_status_help(self):
        """Test racerctl containers status command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "status", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Get the status of a specific container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
    
    def test_racerctl_containers_logs_help(self):
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
    
    def test_racerctl_containers_stop_help(self):
        """Test racerctl containers stop command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "stop", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Stop a running container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
    
    def test_racerctl_containers_remove_help(self):
        """Test racerctl containers remove command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "remove", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Remove a container" in result.stdout
        assert "CONTAINER_ID" in result.stdout
    
    def test_racerctl_containers_cleanup_help(self):
        """Test racerctl containers cleanup command help."""
        result = subprocess.run(
            ["conda", "run", "-n", "racer-dev", "python", "src/client/cli.py", "containers", "cleanup", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "Clean up stopped containers" in result.stdout
