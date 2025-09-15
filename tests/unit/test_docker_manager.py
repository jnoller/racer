"""
Unit tests for Docker manager (final working version).
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
    
    def test_run_container_success(self, mock_docker_client):
        """Test successful container running."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            result = manager.run_container(
                project_name="test-image",
                ports={"8000/tcp": 8000},
                environment={"ENV_VAR": "test_value"}
            )
            
            assert result["success"] is True
            assert result["container_id"] == "test-container-id"
            assert "test-image" in result["container_name"]  # Container name is generated
            assert result["ports"] == {"8000/tcp": 8000}
    
    def test_run_container_failure(self, mock_docker_client):
        """Test container running failure."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock run failure
            mock_docker_client.containers.run.side_effect = Exception("Run failed")
            
            result = manager.run_container(
                project_name="test-image",
                ports={"8000/tcp": 8000}
            )
            
            assert result["success"] is False
            assert "Run failed" in result["error"]
    
    def test_stop_container_success(self, mock_docker_client):
        """Test successful container stopping."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            result = manager.stop_container("test-container-id")
            
            assert result["success"] is True
            assert "Successfully stopped container" in result["message"]
    
    def test_stop_container_failure(self, mock_docker_client):
        """Test container stopping failure."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock stop failure
            mock_docker_client.containers.get.return_value.stop.side_effect = Exception("Stop failed")
            
            result = manager.stop_container("test-container-id")
            
            assert result["success"] is False
            assert "Stop failed" in result["error"]
    
    def test_remove_container_success(self, mock_docker_client):
        """Test successful container removal."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            result = manager.remove_container("test-container-id")
            
            assert result["success"] is True
            assert "Successfully removed container" in result["message"]
    
    def test_remove_container_failure(self, mock_docker_client):
        """Test container removal failure."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock remove failure
            mock_docker_client.containers.get.return_value.remove.side_effect = Exception("Remove failed")
            
            result = manager.remove_container("test-container-id")
            
            assert result["success"] is False
            assert "Remove failed" in result["error"]
    
    def test_port_assignment_automatic(self, mock_docker_client):
        """Test automatic port assignment."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            # Mock port manager
            with patch('src.backend.docker_manager.get_random_port', return_value=8000):
                result = manager.run_container(project_name="test-image")
                
                assert result["success"] is True
                assert result["ports"] == {"8000/tcp": 8000}
    
    def test_port_assignment_custom(self, mock_docker_client):
        """Test custom port assignment."""
        with patch('src.backend.docker_manager.docker.from_env', return_value=mock_docker_client):
            manager = ContainerManager()
            
            custom_ports = {"3000/tcp": 3000, "8080/tcp": 8080}
            result = manager.run_container(
                project_name="test-image",
                ports=custom_ports
            )
            
            assert result["success"] is True
            assert result["ports"] == custom_ports
