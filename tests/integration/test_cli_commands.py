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
    
