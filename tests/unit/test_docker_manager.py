"""
Unit tests for Docker manager.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.backend.docker_manager import ContainerManager


class TestContainerManager:
    """Test cases for ContainerManager class."""
    
    def test_init_success(self, mock_docker_client):
        """Test successful initialization."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            assert manager.client == mock_docker_client
            assert manager.running_containers == {}
            assert manager.container_logs == {}
    
    def test_init_failure(self):
        """Test initialization failure."""
        with patch('src.backend.docker_manager.docker.from_env', side_effect=Exception("Docker not available")):
            with pytest.raises(RuntimeError, match="Failed to connect to Docker"):
                ContainerManager()
    
    def test_build_image_success(self, mock_docker_client, test_project_dir, sample_dockerfile):
        """Test successful image building."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock the dockerfile generation
            with patch('src.backend.dockerfile_template.generate_dockerfile', return_value=sample_dockerfile):
                with patch('src.backend.dockerfile_template.write_dockerfile'):
                    result = manager.build_image(
                        project_path=test_project_dir,
                        project_name="test-image",
                        dockerfile_path=f"{test_project_dir}/Dockerfile"
                    )
            
            assert result["success"] is True
            assert result["image_id"] == "test-image-id"
            assert result["image_tag"] == "test-image"
            assert "Successfully built image test-image" in result["message"]
    
    def test_build_image_failure(self, mock_docker_client, test_project_dir):
        """Test image building failure."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock build failure
            mock_docker_client.images.build.side_effect = Exception("Build failed")
            
            with patch('src.backend.dockerfile_template.generate_dockerfile'):
                with patch('src.backend.dockerfile_template.write_dockerfile'):
                    result = manager.build_image(
                        project_path=test_project_dir,
                        project_name="test-image",
                        dockerfile_path=f"{test_project_dir}/Dockerfile"
                    )
            
            assert result["success"] is False
            assert "Build failed" in result["error"]
    
    def test_run_container_success(self, mock_docker_client):
        """Test successful container running."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            result = manager.run_container(
                project_name="test-image",
                ports={"8000/tcp": 8080},
                environment={"TEST_VAR": "test_value"}
            )
            
            assert result["success"] is True
            assert result["container_id"] == "test-container-id"
            assert result["container_name"].startswith("test-image-")
            assert result["ports"] == {"8000/tcp": 8080}
            assert result["status"] == "running"
            
            # Verify container was added to tracking
            assert "test-container-id" in manager.running_containers
    
    def test_run_container_failure(self, mock_docker_client):
        """Test container running failure."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock run failure
            mock_docker_client.containers.run.side_effect = Exception("Run failed")
            
            result = manager.run_container(project_name="test-image")
            
            assert result["success"] is False
            assert "Run failed" in result["error"]
    
    def test_stop_container_success(self, mock_docker_client):
        """Test successful container stopping."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Add container to tracking
            container_id = "test-container-id"
            manager.running_containers[container_id] = {
                "container": mock_docker_client.containers.run.return_value,
                "container_name": "test-container",
                "project_name": "test-image",
                "ports": {},
                "environment": {},
                "started_at": "2023-01-01T00:00:00",
                "status": "running"
            }
            
            result = manager.stop_container(container_id)
            
            assert result["success"] is True
            assert result["container_id"] == container_id
            assert result["status"] == "stopped"
            
            # Verify container was stopped
            mock_docker_client.containers.run.return_value.stop.assert_called_once()
    
    def test_stop_container_not_found(self, mock_docker_client):
        """Test stopping non-existent container."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            result = manager.stop_container("non-existent-id")
            
            assert result["success"] is False
            assert "Container not found" in result["error"]
    
    def test_remove_container_success(self, mock_docker_client):
        """Test successful container removal."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Add container to tracking
            container_id = "test-container-id"
            manager.running_containers[container_id] = {
                "container": mock_docker_client.containers.run.return_value,
                "container_name": "test-container",
                "project_name": "test-image",
                "ports": {},
                "environment": {},
                "started_at": "2023-01-01T00:00:00",
                "status": "running"
            }
            
            result = manager.remove_container(container_id)
            
            assert result["success"] is True
            assert result["container_id"] == container_id
            assert result["status"] == "removed"
            
            # Verify container was removed from tracking
            assert container_id not in manager.running_containers
    
    def test_get_container_status_success(self, mock_docker_client):
        """Test successful status retrieval."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Add container to tracking
            container_id = "test-container-id"
            manager.running_containers[container_id] = {
                "container": mock_docker_client.containers.run.return_value,
                "container_name": "test-container",
                "project_name": "test-image",
                "ports": {"8000/tcp": 8080},
                "environment": {},
                "started_at": "2023-01-01T00:00:00",
                "status": "running"
            }
            
            result = manager.get_container_status(container_id)
            
            assert result["success"] is True
            assert result["container_id"] == container_id
            assert result["container_name"] == "test-container"
            assert result["status"] == "running"
    
    def test_get_container_logs_success(self, mock_docker_client):
        """Test successful log retrieval."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Add container to tracking
            container_id = "test-container-id"
            manager.running_containers[container_id] = {
                "container": mock_docker_client.containers.run.return_value,
                "container_name": "test-container",
                "project_name": "test-image",
                "ports": {},
                "environment": {},
                "started_at": "2023-01-01T00:00:00",
                "status": "running"
            }
            
            result = manager.get_container_logs(container_id, tail=50)
            
            assert result["success"] is True
            assert result["container_id"] == container_id
            assert result["logs"] == "Test log output"
    
    def test_list_containers_success(self, mock_docker_client):
        """Test successful container listing."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Add container to tracking
            container_id = "test-container-id"
            manager.running_containers[container_id] = {
                "container": mock_docker_client.containers.run.return_value,
                "container_name": "test-container",
                "project_name": "test-image",
                "ports": {"8000/tcp": 8080},
                "environment": {},
                "started_at": "2023-01-01T00:00:00",
                "status": "running"
            }
            
            result = manager.list_containers()
            
            assert result["success"] is True
            assert result["count"] == 1
            assert len(result["containers"]) == 1
            assert result["containers"][0]["container_id"] == container_id
    
    def test_cleanup_stopped_containers(self, mock_docker_client):
        """Test cleanup of stopped containers."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Add stopped container to tracking
            container_id = "test-container-id"
            mock_container = Mock()
            mock_container.status = "exited"
            mock_container.reload = Mock()
            
            manager.running_containers[container_id] = {
                "container": mock_container,
                "container_name": "test-container",
                "project_name": "test-image",
                "ports": {},
                "environment": {},
                "started_at": "2023-01-01T00:00:00",
                "status": "exited"
            }
            
            result = manager.cleanup_stopped_containers()
            
            assert result["success"] is True
            assert result["cleaned_up"] == 1
            assert container_id not in manager.running_containers
