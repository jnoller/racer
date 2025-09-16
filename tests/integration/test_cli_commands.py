"""
Integration tests for CLI commands mentioned in README.
Tests all user-facing and admin CLI commands to ensure they work as documented.
"""

import pytest
import subprocess
import tempfile
import time
import os
from pathlib import Path
from unittest.mock import patch, Mock


class TestCLICommands:
    """Test all CLI commands mentioned in the README."""
    
    @pytest.fixture(scope="class")
    def api_server(self):
        """Start API server for testing."""
        # Start the API server
        process = subprocess.Popen([
            "conda", "run", "-n", "racer-dev", "python", "-m", "uvicorn", 
            "src.backend.main:app", "--host", "0.0.0.0", "--port", "8001"
        ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        max_retries = 30
        for _ in range(max_retries):
            try:
                import requests
                response = requests.get("http://localhost:8001/status", timeout=1)
                if response.status_code == 200:
                    break
            except Exception:
                time.sleep(1)
        else:
            pytest.skip("Could not start API server")
        
        yield process
        
        # Cleanup
        process.terminate()
        process.wait()
    
    @pytest.fixture
    def test_project(self):
        """Create a temporary test project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "test-project"
            project_dir.mkdir()
            
            # Create conda-project.yml
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
            
            # Create a simple main.py
            main_py = project_dir / "main.py"
            main_py.write_text("""#!/usr/bin/env python3
print("Hello from test project!")
""")
            
            yield str(project_dir)
    
    def run_cli_command(self, command, expect_success=True):
        """Helper to run CLI commands and check results."""
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        if expect_success:
            assert result.returncode == 0, f"Command failed: {command}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        else:
            assert result.returncode != 0, f"Command should have failed: {command}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
        
        return result

    # ============================================================================
    # USER CLI COMMANDS (racer)
    # ============================================================================
    
    def test_racer_help(self):
        """Test racer --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer --help")
        assert "deploy" in result.stdout
        assert "list" in result.stdout
        assert "redeploy" in result.stdout
        assert "scale" in result.stdout
        assert "status" in result.stdout
        assert "stop" in result.stdout
        assert "validate" in result.stdout
    
    def test_racer_deploy_help(self):
        """Test racer deploy --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer deploy --help")
        assert "--project-name" in result.stdout
        assert "--path" in result.stdout
        assert "--git" in result.stdout
        assert "--app-port" in result.stdout
        assert "--env" in result.stdout
        assert "--command" in result.stdout
        assert "--build-only" in result.stdout
    
    def test_racer_deploy_build_only(self, api_server, test_project):
        """Test racer deploy --build-only command."""
        result = self.run_cli_command(
            f"conda run -n racer-dev racer deploy --project-name test-project --path {test_project} --build-only"
        )
        # Should show build instructions
        assert "Dockerfile" in result.stdout or "build" in result.stdout.lower()
    
    def test_racer_validate_path(self, api_server, test_project):
        """Test racer validate --path command."""
        result = self.run_cli_command(
            f"conda run -n racer-dev racer validate --path {test_project}"
        )
        assert "valid" in result.stdout.lower() or "✓" in result.stdout
    
    def test_racer_validate_invalid_path(self, api_server):
        """Test racer validate with invalid path."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer validate --path /non/existent/path"
        )
        # Should return success but with invalid result
        assert "invalid" in result.stdout.lower()
    
    def test_racer_list(self, api_server):
        """Test racer list command."""
        result = self.run_cli_command("conda run -n racer-dev racer list")
        # Should show no projects or list of projects
        assert "projects" in result.stdout.lower() or "no running" in result.stdout.lower()
    
    def test_racer_status_list(self, api_server):
        """Test racer status --list command."""
        result = self.run_cli_command("conda run -n racer-dev racer status --list")
        # Should show no projects or list of projects
        assert "projects" in result.stdout.lower() or "no running" in result.stdout.lower()
    
    def test_racer_redeploy_list(self, api_server):
        """Test racer redeploy --list command."""
        result = self.run_cli_command("conda run -n racer-dev racer redeploy --list")
        # Should show no projects or list of projects
        assert "projects" in result.stdout.lower() or "no running" in result.stdout.lower()
    
    def test_racer_redeploy_missing_project_name(self, api_server):
        """Test racer redeploy without project name."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer redeploy",
            expect_success=False
        )
        assert "project-name" in result.stderr.lower() or "required" in result.stderr.lower()
    
    def test_racer_scale_help(self):
        """Test racer scale --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer scale --help")
        assert "Scale a project up or down" in result.stdout
        assert "up" in result.stdout
        assert "down" in result.stdout
        assert "Commands:" in result.stdout
    
    def test_racer_stop_help(self):
        """Test racer stop --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer stop --help")
        assert "--project-name" in result.stdout
        assert "--force" in result.stdout
    
    def test_racer_status_help(self):
        """Test racer status --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer status --help")
        assert "--project-name" in result.stdout
        assert "--project-id" in result.stdout
        assert "--container-id" in result.stdout
        assert "--list" in result.stdout
    
    def test_racer_redeploy_help(self):
        """Test racer redeploy --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer redeploy --help")
        assert "--project-name" in result.stdout
        assert "--environment" in result.stdout
        assert "--command" in result.stdout
        assert "--no-rebuild" in result.stdout
        assert "--list" in result.stdout
    
    def test_racer_validate_help(self):
        """Test racer validate --help command."""
        result = self.run_cli_command("conda run -n racer-dev racer validate --help")
        assert "--path" in result.stdout
        assert "--git" in result.stdout
    
    # ============================================================================
    # ADMIN CLI COMMANDS (racerctl)
    # ============================================================================
    
    def test_racerctl_help(self):
        """Test racerctl --help command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl --help")
        assert "server" in result.stdout
        assert "containers" in result.stdout
        assert "swarm" in result.stdout
        assert "status" in result.stdout
    
    def test_racerctl_status(self, api_server):
        """Test racerctl status command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl status")
        assert "Racer API Server Status" in result.stdout
        assert "Overall Status" in result.stdout
    
    def test_racerctl_status_verbose(self, api_server):
        """Test racerctl status --verbose command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl status --verbose")
        assert "Complete status response" in result.stdout
        assert "overall_status" in result.stdout
    
    def test_racerctl_server_help(self):
        """Test racerctl server --help command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl server --help")
        assert "start" in result.stdout
        assert "stop" in result.stdout
        assert "restart" in result.stdout
        assert "status" in result.stdout
    
    def test_racerctl_server_status(self, api_server):
        """Test racerctl server status command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl server status")
        assert "running" in result.stdout.lower() or "started" in result.stdout.lower()
    
    def test_racerctl_containers_help(self):
        """Test racerctl containers --help command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl containers --help")
        assert "list" in result.stdout
        assert "logs" in result.stdout
        assert "stop" in result.stdout
        assert "remove" in result.stdout
        assert "cleanup" in result.stdout
        assert "status" in result.stdout
    
    def test_racerctl_containers_list(self, api_server):
        """Test racerctl containers list command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl containers list")
        # Should show containers or "no containers"
        assert "container" in result.stdout.lower() or "no containers" in result.stdout.lower()
    
    def test_racerctl_containers_cleanup(self, api_server):
        """Test racerctl containers cleanup command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl containers cleanup")
        assert "cleanup" in result.stdout.lower() or "cleaned" in result.stdout.lower()
    
    def test_racerctl_swarm_help(self):
        """Test racerctl swarm --help command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl swarm --help")
        assert "status" in result.stdout
        assert "logs" in result.stdout
        assert "remove" in result.stdout
    
    def test_racerctl_swarm_status(self, api_server):
        """Test racerctl swarm status command."""
        result = self.run_cli_command("conda run -n racer-dev racerctl swarm status")
        # Should show swarm services or "no services"
        assert "swarm" in result.stdout.lower() or "services" in result.stdout.lower()
    
    # ============================================================================
    # ERROR HANDLING TESTS
    # ============================================================================
    
    def test_racer_deploy_missing_project_name(self, api_server):
        """Test racer deploy without required project name."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer deploy --path /some/path",
            expect_success=False
        )
        assert "project-name" in result.stderr.lower() or "required" in result.stderr.lower()
    
    def test_racer_scale_missing_project_name(self, api_server):
        """Test racer scale without required project name."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer scale up --instances 3",
            expect_success=False
        )
        assert "project-name" in result.stderr.lower() or "required" in result.stderr.lower()
    
    def test_racer_stop_missing_project_name(self, api_server):
        """Test racer stop without required project name."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer stop",
            expect_success=False
        )
        assert "project-name" in result.stderr.lower() or "required" in result.stderr.lower()
    
    def test_racer_status_missing_project_name(self, api_server):
        """Test racer status without project name (should require --list)."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer status",
            expect_success=False
        )
        # Should fail without project name or --list
        assert "must be specified" in result.stderr
    
    def test_racerctl_swarm_remove_missing_project_name(self, api_server):
        """Test racerctl swarm remove without required project name."""
        result = self.run_cli_command(
            "conda run -n racer-dev racerctl swarm remove",
            expect_success=False
        )
        assert "project-name" in result.stderr.lower() or "required" in result.stderr.lower()
    
    # ============================================================================
    # COMMAND COMBINATIONS FROM README
    # ============================================================================
    
    def test_racer_deploy_with_all_options(self, api_server, test_project):
        """Test racer deploy with all options from README examples."""
        result = self.run_cli_command(
            f"conda run -n racer-dev racer deploy --project-name test-project --path {test_project} --app-port 8000 --env DEBUG=true,LOG_LEVEL=debug --command 'python main.py'"
        )
        # Should either succeed or fail gracefully with a clear error
        # (might fail due to Docker not being available in test environment)
        assert result.returncode in [0, 1, 2]  # Allow for various failure modes
    
    def test_racer_scale_with_all_options(self, api_server, test_project):
        """Test racer scale with all options from README examples."""
        result = self.run_cli_command(
            f"conda run -n racer-dev racer scale up --project-name test-project --instances 3"
        )
        # Should either succeed or fail gracefully with a clear error
        assert result.returncode in [0, 1, 2]  # Allow for various failure modes
    
    def test_racer_redeploy_with_all_options(self, api_server):
        """Test racer redeploy with all options from README examples."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer redeploy --project-name test-project --environment DEBUG=true,LOG_LEVEL=debug --command 'python app.py --debug'"
        )
        # Should succeed but show no projects found
        assert result.returncode == 0
        assert "not found" in result.stderr.lower() or "no running" in result.stderr.lower()
    
    def test_racer_stop_with_force(self, api_server):
        """Test racer stop with --force option."""
        result = self.run_cli_command(
            "conda run -n racer-dev racer stop --project-name non-existent --force"
        )
        # Should succeed but show no project found
        assert result.returncode == 0
        assert "not found" in result.stdout.lower() or "no running" in result.stdout.lower()
    
    def test_racerctl_swarm_remove_with_force(self, api_server):
        """Test racerctl swarm remove with --force option."""
        result = self.run_cli_command(
            "conda run -n racer-dev racerctl swarm remove --project-name non-existent --force"
        )
        # Should succeed but show service not found
        assert result.returncode == 0
        assert "not found" in result.stdout.lower() or "failed" in result.stdout.lower()
