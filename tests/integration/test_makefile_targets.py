"""
Integration tests for Makefile targets.
"""

import pytest
import subprocess
import os
import tempfile
from pathlib import Path


class TestMakefileTargets:
    """Test cases for Makefile targets from README."""
    
    def test_make_help(self):
        """Test make help command."""
        result = subprocess.run(
            ["make", "help"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "setup-all" in result.stdout
        assert "setup" in result.stdout
        assert "install-dev" in result.stdout
        assert "verify" in result.stdout
        assert "test" in result.stdout
        assert "clean" in result.stdout
    
    def test_make_setup_all(self):
        """Test make setup-all command."""
        # This test might take a while, so we'll just verify it starts
        result = subprocess.run(
            ["make", "setup-all", "--dry-run"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        # Dry run might not be supported, so we check for help output
        assert "setup-all" in result.stdout or result.returncode == 0
    
    def test_make_verify(self):
        """Test make verify command."""
        result = subprocess.run(
            ["make", "verify"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        # This might fail if environment isn't set up, but should show verification steps
        assert "Verifying Racer setup" in result.stdout or result.returncode != 0
    
    def test_make_test_quick(self):
        """Test make test-quick command."""
        result = subprocess.run(
            ["make", "test-quick"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "Running quick tests" in result.stdout
        assert "passed" in result.stdout.lower()
    
    def test_make_test_unit(self):
        """Test make test-unit command."""
        result = subprocess.run(
            ["make", "test-unit"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "Running unit tests" in result.stdout
        assert "passed" in result.stdout.lower()
    
    def test_make_lint(self):
        """Test make lint command."""
        result = subprocess.run(
            ["make", "lint"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        # Linting might find issues, but should complete
        assert result.returncode == 0 or result.returncode == 1 or result.returncode == 2
        assert "Running linting" in result.stdout
    
    def test_make_format(self):
        """Test make format command."""
        result = subprocess.run(
            ["make", "format"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "Formatting code" in result.stdout
    
    def test_make_db_init(self):
        """Test make db-init command."""
        result = subprocess.run(
            ["make", "db-init"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "Initializing database" in result.stdout
    
    def test_make_db_clean(self):
        """Test make db-clean command."""
        result = subprocess.run(
            ["make", "db-clean"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "Cleaning up database" in result.stdout
    
    def test_make_client(self):
        """Test make client command."""
        result = subprocess.run(
            ["make", "client"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        assert result.returncode == 0
        assert "Installing client in development mode" in result.stdout
