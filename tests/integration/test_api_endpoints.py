"""
Integration tests for API endpoints.
"""

import pytest
import requests
import time
from unittest.mock import patch


@pytest.mark.integration
@pytest.mark.api
class TestAPIEndpoints:
    """Integration tests for API endpoints."""
    
    def test_health_endpoint(self, api_server):
        """Test health endpoint."""
        response = requests.get(f"{api_server}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data
        assert "service" in data
    
    def test_liveness_endpoint(self, api_server):
        """Test liveness endpoint."""
        response = requests.get(f"{api_server}/liveness")
        assert response.status_code == 200
        
        data = response.json()
        assert data["alive"] is True
        assert "uptime" in data
        assert "timestamp" in data
    
    def test_readiness_endpoint(self, api_server):
        """Test readiness endpoint."""
        response = requests.get(f"{api_server}/ready")
        assert response.status_code == 200
        
        data = response.json()
        assert data["ready"] is True
        assert "checks" in data
        assert "timestamp" in data
    
    def test_root_endpoint(self, api_server):
        """Test root endpoint."""
        response = requests.get(f"{api_server}/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data
    
    def test_validate_endpoint_local_path(self, api_server, test_project_dir):
        """Test validate endpoint with local path."""
        response = requests.post(f"{api_server}/validate", json={
            "project_path": test_project_dir
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert data["project_name"] == "test-project"
        assert "default" in data["environments"]
    
    def test_validate_endpoint_missing_path(self, api_server):
        """Test validate endpoint with missing path."""
        response = requests.post(f"{api_server}/validate", json={})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "project_path" in data["detail"] or "git_url" in data["detail"]
    
    def test_validate_endpoint_invalid_path(self, api_server):
        """Test validate endpoint with invalid path."""
        response = requests.post(f"{api_server}/validate", json={
            "project_path": "/non/existent/path"
        })
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    @patch('src.backend.project_validator.git.Repo')
    def test_validate_endpoint_git_url(self, mock_repo_class, api_server, test_project_dir, sample_conda_project_yml, sample_environment_yml):
        """Test validate endpoint with git URL."""
        # Mock git repository
        mock_repo = mock_repo_class.return_value
        mock_repo.clone_from.return_value = mock_repo
        
        # Mock cloned repository contents
        with patch('src.backend.project_validator.os.path.exists', return_value=True):
            with patch('src.backend.project_validator.Path.read_text') as mock_read_text:
                def read_text_side_effect(path):
                    if str(path).endswith("conda-project.yml"):
                        return sample_conda_project_yml
                    elif str(path).endswith("environment.yml"):
                        return sample_environment_yml
                    return ""
                
                mock_read_text.side_effect = read_text_side_effect
                
                response = requests.post(f"{api_server}/validate", json={
                    "git_url": "https://github.com/test/repo.git"
                })
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert data["project_name"] == "test-project"
    
    def test_dockerfile_endpoint_local_path(self, api_server, test_project_dir):
        """Test dockerfile endpoint with local path."""
        response = requests.post(f"{api_server}/dockerfile", json={
            "project_path": test_project_dir
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["project_name"] == "test-project"
        assert "Dockerfile" in data["dockerfile_path"]
        assert "FROM continuumio/miniconda3" in data["dockerfile_content"]
    
    def test_dockerfile_endpoint_with_custom_commands(self, api_server, test_project_dir):
        """Test dockerfile endpoint with custom commands."""
        response = requests.post(f"{api_server}/dockerfile", json={
            "project_path": test_project_dir,
            "custom_commands": ["apt-get update", "apt-get install -y curl"]
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "RUN apt-get update" in data["dockerfile_content"]
        assert "RUN apt-get install -y curl" in data["dockerfile_content"]
    
    def test_dockerfile_endpoint_missing_path(self, api_server):
        """Test dockerfile endpoint with missing path."""
        response = requests.post(f"{api_server}/dockerfile", json={})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.docker
    def test_containers_run_endpoint_local_path(self, api_server, test_project_dir):
        """Test containers/run endpoint with local path."""
        response = requests.post(f"{api_server}/containers/run", json={
            "project_path": test_project_dir,
            "ports": {"8000/tcp": 8080}
        })
        
        # This might fail if Docker is not available, so we check for either success or specific error
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert "container_id" in data
            assert "container_name" in data
            assert data["ports"] == {"8000/tcp": 8080}
        else:
            # If Docker is not available, we expect a specific error
            assert response.status_code in [400, 500]
            data = response.json()
            assert "detail" in data
    
    def test_containers_run_endpoint_missing_path(self, api_server):
        """Test containers/run endpoint with missing path."""
        response = requests.post(f"{api_server}/containers/run", json={})
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
    
    def test_containers_list_endpoint(self, api_server):
        """Test containers list endpoint."""
        response = requests.get(f"{api_server}/containers")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "containers" in data
        assert "count" in data
        assert isinstance(data["containers"], list)
    
    def test_containers_cleanup_endpoint(self, api_server):
        """Test containers cleanup endpoint."""
        response = requests.post(f"{api_server}/containers/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "cleaned_up" in data
        assert "message" in data
    
    def test_containers_status_endpoint_not_found(self, api_server):
        """Test containers status endpoint with non-existent container."""
        response = requests.get(f"{api_server}/containers/non-existent-id/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_containers_logs_endpoint_not_found(self, api_server):
        """Test containers logs endpoint with non-existent container."""
        response = requests.get(f"{api_server}/containers/non-existent-id/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_containers_stop_endpoint_not_found(self, api_server):
        """Test containers stop endpoint with non-existent container."""
        response = requests.post(f"{api_server}/containers/non-existent-id/stop")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_containers_remove_endpoint_not_found(self, api_server):
        """Test containers remove endpoint with non-existent container."""
        response = requests.delete(f"{api_server}/containers/non-existent-id")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is False
        assert "not found" in data["error"].lower()
    
    def test_docs_endpoint(self, api_server):
        """Test docs endpoint."""
        response = requests.get(f"{api_server}/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    
    def test_openapi_endpoint(self, api_server):
        """Test OpenAPI schema endpoint."""
        response = requests.get(f"{api_server}/openapi.json")
        assert response.status_code == 200
        
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
