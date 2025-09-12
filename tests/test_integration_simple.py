"""
Simple integration tests for Racer API.
"""

import pytest
import requests
import time
import subprocess
import os
import tempfile
from pathlib import Path


@pytest.mark.integration
def test_api_health_endpoint():
    """Test that the API health endpoint works."""
    # Start the API server
    process = subprocess.Popen([
        "conda", "run", "-n", "racer", "python", "-m", "uvicorn", 
        "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"
    ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
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
            pytest.skip("Could not start API server")
        
        # Test health endpoint
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        
    finally:
        # Cleanup
        process.terminate()
        process.wait()


@pytest.mark.integration
def test_api_root_endpoint():
    """Test that the API root endpoint works."""
    # Start the API server
    process = subprocess.Popen([
        "conda", "run", "-n", "racer", "python", "-m", "uvicorn", 
        "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"
    ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        # Wait for server to start
        max_retries = 30
        for _ in range(max_retries):
            try:
                response = requests.get("http://localhost:8000/", timeout=1)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            pytest.skip("Could not start API server")
        
        # Test root endpoint
        response = requests.get("http://localhost:8000/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        
    finally:
        # Cleanup
        process.terminate()
        process.wait()


@pytest.mark.integration
def test_api_validate_endpoint():
    """Test that the API validate endpoint works."""
    # Start the API server
    process = subprocess.Popen([
        "conda", "run", "-n", "racer", "python", "-m", "uvicorn", 
        "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"
    ], cwd=os.getcwd(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
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
            pytest.skip("Could not start API server")
        
        # Create a test project
        with tempfile.TemporaryDirectory() as temp_dir:
            project_dir = Path(temp_dir) / "test-project"
            project_dir.mkdir()
            
            # Create conda-project.yml
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
            
            # Test validate endpoint
            response = requests.post("http://localhost:8000/validate", json={
                "project_path": str(project_dir)
            })
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
            assert data["project_name"] == "test-project"
            
    finally:
        # Cleanup
        process.terminate()
        process.wait()
