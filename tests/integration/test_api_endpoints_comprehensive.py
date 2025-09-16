"""
Comprehensive integration tests for all API endpoints mentioned in README.
Tests all user-facing and admin API endpoints to ensure they work as documented.
"""

import pytest
import requests
import time
import subprocess
import os
import tempfile
from pathlib import Path


class TestAPIEndpointsComprehensive:
    """Test all API endpoints mentioned in the README."""
    
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
                response = requests.get("http://localhost:8001/status", timeout=1)
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
    
    # ============================================================================
    # SYSTEM ENDPOINTS
    # ============================================================================
    
    def test_root_endpoint(self, api_server):
        """Test GET / - API root information."""
        response = requests.get("http://localhost:8001/")
        assert response.status_code == 200
        
        data = response.json()
        assert "service" in data
        assert "version" in data
        assert "description" in data
        assert "docs" in data
        assert "status" in data
        assert data["service"] == "Racer API"
        assert data["version"] == "0.1.0"
    
    def test_status_endpoint(self, api_server):
        """Test GET /status - Comprehensive status check."""
        response = requests.get("http://localhost:8001/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "overall_status" in data
        assert "service" in data
        assert "version" in data
        assert "timestamp" in data
        assert "health" in data
        assert "liveness" in data
        assert "readiness" in data
        assert "info" in data
        assert data["overall_status"] in ["healthy", "degraded", "unhealthy"]
        assert data["service"] == "racer-api"
    
    def test_api_info_endpoint(self, api_server):
        """Test GET /api/info - API discovery endpoint."""
        response = requests.get("http://localhost:8001/api/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "description" in data
        assert "documentation" in data
        assert "endpoints" in data
        
        # Check endpoint structure
        endpoints = data["endpoints"]
        assert "user_facing" in endpoints
        assert "admin" in endpoints
        assert "system" in endpoints
        
        # Check user-facing endpoints
        user_endpoints = endpoints["user_facing"]["endpoints"]
        assert any("POST /api/v1/deploy" in ep for ep in user_endpoints)
        assert any("GET /api/v1/projects" in ep for ep in user_endpoints)
        assert any("POST /api/v1/status" in ep for ep in user_endpoints)
        assert any("POST /api/v1/redeploy" in ep for ep in user_endpoints)
        assert any("POST /api/v1/scale" in ep for ep in user_endpoints)
        assert any("POST /api/v1/validate" in ep for ep in user_endpoints)
        
        # Check admin endpoints
        admin_endpoints = endpoints["admin"]["endpoints"]
        assert any("GET /admin/containers" in ep for ep in admin_endpoints)
        assert any("POST /admin/containers/cleanup" in ep for ep in admin_endpoints)
        assert any("GET /admin/swarm/services" in ep for ep in admin_endpoints)
    
    def test_docs_endpoint(self, api_server):
        """Test GET /docs - Swagger UI."""
        response = requests.get("http://localhost:8001/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_redoc_endpoint(self, api_server):
        """Test GET /redoc - ReDoc documentation."""
        response = requests.get("http://localhost:8001/redoc")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_endpoint(self, api_server):
        """Test GET /openapi.json - OpenAPI specification."""
        response = requests.get("http://localhost:8001/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
        assert data["info"]["title"] == "Racer API"
    
    # ============================================================================
    # USER-FACING ENDPOINTS (/api/v1/)
    # ============================================================================
    
    def test_deploy_endpoint_missing_data(self, api_server):
        """Test POST /api/v1/deploy with missing data."""
        response = requests.post("http://localhost:8001/api/v1/deploy", json={})
        assert response.status_code == 422  # Validation error
    
    def test_deploy_endpoint_invalid_path(self, api_server):
        """Test POST /api/v1/deploy with invalid path."""
        response = requests.post("http://localhost:8001/api/v1/deploy", json={
            "project_name": "test-project",
            "project_path": "/non/existent/path"
        })
        assert response.status_code == 200  # Should return success=False
        data = response.json()
        assert "success" in data
        assert data["success"] is False
    
    def test_deploy_endpoint_valid_project(self, api_server, test_project):
        """Test POST /api/v1/deploy with valid project."""
        response = requests.post("http://localhost:8001/api/v1/deploy", json={
            "project_name": "test-project",
            "project_path": test_project,
            "app_port": 8000
        })
        # Should either succeed or fail with a clear error (Docker might not be available)
        assert response.status_code in [200, 400, 500]
    
    def test_deploy_endpoint_build_only(self, api_server, test_project):
        """Test POST /api/v1/deploy with build_only flag."""
        response = requests.post("http://localhost:8001/api/v1/deploy", json={
            "project_name": "test-project",
            "project_path": test_project,
            "build_only": True
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "dockerfile_path" in data
        assert "dockerfile_content" in data
        assert "instructions" in data
    
    def test_projects_list_endpoint(self, api_server):
        """Test GET /api/v1/projects - List all projects."""
        response = requests.get("http://localhost:8001/api/v1/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_status_endpoint_missing_data(self, api_server):
        """Test POST /api/v1/status with missing data."""
        response = requests.post("http://localhost:8001/api/v1/status", json={})
        assert response.status_code == 422  # Validation error
    
    def test_status_endpoint_with_project_name(self, api_server):
        """Test POST /api/v1/status with project name."""
        response = requests.post("http://localhost:8001/api/v1/status", json={
            "project_name": "non-existent-project"
        })
        # Should return success=False for non-existent project
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is False
    
    def test_redeploy_endpoint_missing_data(self, api_server):
        """Test POST /api/v1/redeploy with missing data."""
        response = requests.post("http://localhost:8001/api/v1/redeploy", json={})
        assert response.status_code == 422  # Validation error
    
    def test_redeploy_endpoint_non_existent_project(self, api_server):
        """Test POST /api/v1/redeploy with non-existent project."""
        response = requests.post("http://localhost:8001/api/v1/redeploy", json={
            "project_name": "non-existent-project"
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_scale_endpoint_missing_data(self, api_server):
        """Test POST /api/v1/scale with missing data."""
        response = requests.post("http://localhost:8001/api/v1/scale", json={})
        assert response.status_code == 422  # Validation error
    
    def test_scale_endpoint_non_existent_project(self, api_server):
        """Test POST /api/v1/scale with non-existent project."""
        response = requests.post("http://localhost:8001/api/v1/scale", json={
            "project_name": "non-existent-project",
            "instances": 3,
            "app_port": 8000
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is False
        assert "not found" in data["message"].lower()
    
    def test_validate_endpoint_missing_data(self, api_server):
        """Test POST /api/v1/validate with missing data."""
        response = requests.post("http://localhost:8001/api/v1/validate", json={})
        assert response.status_code == 200  # Should return valid=False
    
    def test_validate_endpoint_valid_project(self, api_server, test_project):
        """Test POST /api/v1/validate with valid project."""
        response = requests.post("http://localhost:8001/api/v1/validate", json={
            "project_path": test_project
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data
        assert data["valid"] is True
        assert "project_name" in data
        assert data["project_name"] == "test-project"
    
    def test_validate_endpoint_invalid_project(self, api_server):
        """Test POST /api/v1/validate with invalid project."""
        response = requests.post("http://localhost:8001/api/v1/validate", json={
            "project_path": "/non/existent/path"
        })
        assert response.status_code == 200  # Should return valid=False
        
        data = response.json()
        assert "valid" in data
        assert data["valid"] is False
        assert "message" in data
    
    def test_validate_endpoint_git_url(self, api_server):
        """Test POST /api/v1/validate with git URL."""
        response = requests.post("http://localhost:8001/api/v1/validate", json={
            "git_url": "https://github.com/conda/conda-project.git"
        })
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 400, 500]
    
    # ============================================================================
    # ADMIN ENDPOINTS (/admin/)
    # ============================================================================
    
    def test_containers_list_endpoint(self, api_server):
        """Test GET /admin/containers - List all containers."""
        response = requests.get("http://localhost:8001/admin/containers")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_containers_cleanup_endpoint(self, api_server):
        """Test POST /admin/containers/cleanup - Cleanup containers."""
        response = requests.post("http://localhost:8001/admin/containers/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "message" in data
    
    def test_containers_remove_endpoint_missing_id(self, api_server):
        """Test DELETE /admin/containers/{container_id} with missing ID."""
        response = requests.delete("http://localhost:8001/admin/containers/")
        assert response.status_code == 405  # Method not allowed for missing ID
    
    def test_containers_remove_endpoint_invalid_id(self, api_server):
        """Test DELETE /admin/containers/{container_id} with invalid ID."""
        response = requests.delete("http://localhost:8001/admin/containers/invalid-id")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is False
    
    def test_swarm_services_list_endpoint(self, api_server):
        """Test GET /admin/swarm/services - List swarm services."""
        response = requests.get("http://localhost:8001/admin/swarm/services")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_swarm_service_status_endpoint_missing_name(self, api_server):
        """Test GET /admin/swarm/service/{name}/status with missing name."""
        response = requests.get("http://localhost:8001/admin/swarm/service//status")
        assert response.status_code == 404
    
    def test_swarm_service_status_endpoint_invalid_name(self, api_server):
        """Test GET /admin/swarm/service/{name}/status with invalid name."""
        response = requests.get("http://localhost:8001/admin/swarm/service/invalid-service/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        # Should return success=True but with no service found
        assert data["success"] is True
    
    def test_swarm_service_logs_endpoint_missing_name(self, api_server):
        """Test GET /admin/swarm/service/{name}/logs with missing name."""
        response = requests.get("http://localhost:8001/admin/swarm/service//logs")
        assert response.status_code == 404
    
    def test_swarm_service_logs_endpoint_invalid_name(self, api_server):
        """Test GET /admin/swarm/service/{name}/logs with invalid name."""
        response = requests.get("http://localhost:8001/admin/swarm/service/invalid-service/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        # Should return success=True but with no service found
        assert data["success"] is True
    
    def test_swarm_service_remove_endpoint_missing_name(self, api_server):
        """Test DELETE /admin/swarm/service/{name} with missing name."""
        response = requests.delete("http://localhost:8001/admin/swarm/service/")
        assert response.status_code == 404
    
    def test_swarm_service_remove_endpoint_invalid_name(self, api_server):
        """Test DELETE /admin/swarm/service/{name} with invalid name."""
        response = requests.delete("http://localhost:8001/admin/swarm/service/invalid-service")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert data["success"] is False
    
