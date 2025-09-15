"""
Comprehensive API endpoint tests covering all README endpoints.
"""

import pytest
import requests
import time
import subprocess
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock


class TestAPIEndpointsComprehensive:
    """Test cases for all API endpoints from README."""
    
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
                response = requests.get("http://localhost:8001/health", timeout=1)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            pytest.skip("Could not start API server")
        
        yield process
        
        # Cleanup
        process.terminate()
        process.wait()
    
    def test_root_endpoint(self, api_server):
        """Test GET / endpoint."""
        response = requests.get("http://localhost:8001/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
        assert "health" in data
    
    def test_health_endpoint(self, api_server):
        """Test GET /health endpoint."""
        response = requests.get("http://localhost:8001/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "service" in data
    
    def test_liveness_endpoint(self, api_server):
        """Test GET /liveness endpoint."""
        response = requests.get("http://localhost:8001/liveness")
        assert response.status_code == 200
        
        data = response.json()
        assert data["alive"] is True
        assert "timestamp" in data
        assert "uptime" in data
    
    def test_readiness_endpoint(self, api_server):
        """Test GET /ready endpoint."""
        response = requests.get("http://localhost:8001/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data
    
    def test_validate_endpoint_success(self, api_server):
        """Test POST /validate endpoint with valid project."""
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
            
            # Test validate endpoint
            response = requests.post("http://localhost:8001/validate", json={
                "project_path": str(project_dir)
            })
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["valid"] is True
            assert data["project_name"] == "test-project"
    
    def test_validate_endpoint_invalid_project(self, api_server):
        """Test POST /validate endpoint with invalid project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with empty directory
            response = requests.post("http://localhost:8001/validate", json={
                "project_path": temp_dir
            })
            
            assert response.status_code == 400
            
            data = response.json()
            assert data["valid"] is False
            assert "conda-project.yml" in data["error"]
    
    def test_dockerfile_endpoint_success(self, api_server):
        """Test POST /dockerfile endpoint with valid project."""
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
            
            # Test dockerfile endpoint
            response = requests.post("http://localhost:8001/dockerfile", json={
                "project_path": str(project_dir)
            })
            
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "dockerfile_content" in data
            assert "FROM continuumio/miniconda3" in data["dockerfile_content"]
    
    def test_containers_list_endpoint(self, api_server):
        """Test GET /containers endpoint."""
        response = requests.get("http://localhost:8001/containers")
        assert response.status_code == 200
        
        data = response.json()
        assert "containers" in data
        assert "count" in data
    
    def test_containers_run_endpoint_missing_data(self, api_server):
        """Test POST /containers/run endpoint with missing data."""
        response = requests.post("http://localhost:8001/containers/run", json={})
        assert response.status_code == 422  # Validation error
    
    def test_containers_run_endpoint_invalid_path(self, api_server):
        """Test POST /containers/run endpoint with invalid path."""
        response = requests.post("http://localhost:8001/containers/run", json={
            "project_name": "test-project",
            "project_path": "/non/existent/path"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert "Project path does not exist" in data["detail"]
    
    def test_containers_status_endpoint_missing_container(self, api_server):
        """Test GET /containers/{id}/status endpoint with missing container."""
        response = requests.get("http://localhost:8001/containers/nonexistent/status")
        assert response.status_code == 404
    
    def test_containers_logs_endpoint_missing_container(self, api_server):
        """Test GET /containers/{id}/logs endpoint with missing container."""
        response = requests.get("http://localhost:8001/containers/nonexistent/logs")
        assert response.status_code == 404
    
    def test_containers_stop_endpoint_missing_container(self, api_server):
        """Test POST /containers/{id}/stop endpoint with missing container."""
        response = requests.post("http://localhost:8001/containers/nonexistent/stop")
        assert response.status_code == 404
    
    def test_containers_remove_endpoint_missing_container(self, api_server):
        """Test DELETE /containers/{id} endpoint with missing container."""
        response = requests.delete("http://localhost:8001/containers/nonexistent")
        assert response.status_code == 404
    
    def test_containers_cleanup_endpoint(self, api_server):
        """Test POST /containers/cleanup endpoint."""
        response = requests.post("http://localhost:8001/containers/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert "cleaned_up" in data
        assert "message" in data
    
    def test_projects_list_endpoint(self, api_server):
        """Test GET /projects endpoint."""
        response = requests.get("http://localhost:8001/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert "projects" in data
        assert "count" in data
    
    def test_projects_status_endpoint_missing_data(self, api_server):
        """Test POST /projects/status endpoint with missing data."""
        response = requests.post("http://localhost:8001/projects/status", json={})
        assert response.status_code == 422  # Validation error
    
    def test_projects_status_by_id_endpoint_missing_data(self, api_server):
        """Test POST /projects/status-by-id endpoint with missing data."""
        response = requests.post("http://localhost:8001/projects/status-by-id", json={})
        assert response.status_code == 422  # Validation error
    
    def test_projects_rerun_endpoint_missing_data(self, api_server):
        """Test POST /projects/rerun endpoint with missing data."""
        response = requests.post("http://localhost:8001/projects/rerun", json={})
        assert response.status_code == 422  # Validation error
    
    def test_projects_scale_endpoint_missing_data(self, api_server):
        """Test POST /projects/scale endpoint with missing data."""
        response = requests.post("http://localhost:8001/projects/scale", json={})
        assert response.status_code == 422  # Validation error
    
    def test_projects_scale_up_endpoint_missing_data(self, api_server):
        """Test POST /projects/scale-up endpoint with missing data."""
        response = requests.post("http://localhost:8001/projects/scale-up", json={})
        assert response.status_code == 422  # Validation error
    
    def test_projects_scale_down_endpoint_missing_data(self, api_server):
        """Test POST /projects/scale-down endpoint with missing data."""
        response = requests.post("http://localhost:8001/projects/scale-down", json={})
        assert response.status_code == 422  # Validation error
    
    def test_swarm_services_list_endpoint(self, api_server):
        """Test GET /swarm/services endpoint."""
        response = requests.get("http://localhost:8001/swarm/services")
        assert response.status_code == 200
        
        data = response.json()
        assert "services" in data
        assert "count" in data
    
    def test_swarm_service_status_endpoint_missing_data(self, api_server):
        """Test GET /swarm/service/{name}/status endpoint with missing data."""
        response = requests.get("http://localhost:8001/swarm/service/status")
        assert response.status_code == 404  # Missing service name
    
    def test_swarm_service_logs_endpoint_missing_data(self, api_server):
        """Test GET /swarm/service/{name}/logs endpoint with missing data."""
        response = requests.get("http://localhost:8001/swarm/service/logs")
        assert response.status_code == 404  # Missing service name
    
    def test_swarm_service_remove_endpoint_missing_data(self, api_server):
        """Test DELETE /swarm/service/{name} endpoint with missing data."""
        response = requests.delete("http://localhost:8001/swarm/service/remove")
        assert response.status_code == 404  # Missing service name
    
    def test_swarm_service_scale_endpoint_missing_data(self, api_server):
        """Test POST /swarm/service/scale endpoint with missing data."""
        response = requests.post("http://localhost:8001/swarm/service/scale", json={})
        assert response.status_code == 422  # Validation error
    
    def test_swarm_service_create_endpoint_missing_data(self, api_server):
        """Test POST /swarm/service/create endpoint with missing data."""
        response = requests.post("http://localhost:8001/swarm/service/create", json={})
        assert response.status_code == 422  # Validation error
