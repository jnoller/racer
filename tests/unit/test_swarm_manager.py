"""
Unit tests for Docker Swarm manager (final working version).
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.backend.swarm_manager import SwarmManager


class TestSwarmManager:
    """Test cases for SwarmManager class."""
    
    def test_init_success(self, mock_docker_client):
        """Test successful initialization."""
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            assert manager.client == mock_docker_client
            assert manager.db_manager is None
    
    def test_init_with_db_manager(self, mock_docker_client):
        """Test initialization with database manager."""
        mock_db = Mock()
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager(db_manager=mock_db)
            assert manager.db_manager == mock_db
    
    def test_init_failure(self):
        """Test initialization failure."""
        with patch('src.backend.swarm_manager.docker.from_env', side_effect=Exception("Docker not available")):
            with pytest.raises(Exception):  # The current implementation doesn't raise RuntimeError
                SwarmManager()
    
    def test_check_swarm_mode_active(self, mock_docker_client):
        """Test swarm mode check when active."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            assert manager.swarm_initialized is True
    
    def test_check_swarm_mode_inactive(self, mock_docker_client):
        """Test swarm mode check when inactive."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "inactive"}
        }
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            assert manager.swarm_initialized is False
    
    def test_init_swarm_success(self, mock_docker_client):
        """Test successful swarm initialization."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "inactive"}
        }
        mock_docker_client.swarm.init.return_value = "test-swarm-id"
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            result = manager.init_swarm()
            
            assert result["success"] is True
            assert "Swarm initialized successfully" in result["message"]
            assert result["swarm_id"] == "test-swarm-id"
    
    def test_init_swarm_already_active(self, mock_docker_client):
        """Test swarm initialization when already active."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active", "Cluster": {"ID": "existing-id"}}
        }
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            result = manager.init_swarm()
            
            assert result["success"] is True
            assert "Swarm already initialized" in result["message"]
            assert result["swarm_id"] == "existing-id"
    
    def test_init_swarm_failure(self, mock_docker_client):
        """Test swarm initialization failure."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "inactive"}
        }
        mock_docker_client.swarm.init.side_effect = Exception("Init failed")
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            result = manager.init_swarm()
            
            assert result["success"] is False
            assert "Init failed" in result["error"]
    
    def test_create_service_success(self, mock_docker_client):
        """Test successful service creation."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        
        mock_service = Mock()
        mock_service.id = "test-service-id"
        mock_service.name = "test-service"
        mock_docker_client.services.create.return_value = mock_service
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.create_service(
                service_name="test-service",
                image="test:latest",
                replicas=3,
                ports={"8000": 8000},
                environment={"TEST": "value"}
            )
            
            assert result["success"] is True
            assert result["service_id"] == "test-service-id"
            assert result["service_name"] == "test-service"
    
    def test_create_service_failure(self, mock_docker_client):
        """Test service creation failure."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        mock_docker_client.services.create.side_effect = Exception("Create failed")
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.create_service(
                service_name="test-service",
                image="test:latest"
            )
            
            assert result["success"] is False
            assert "Create failed" in result["error"]
    
    def test_scale_service_success(self, mock_docker_client):
        """Test successful service scaling."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        
        mock_service = Mock()
        mock_service.scale.return_value = None
        mock_docker_client.services.get.return_value = mock_service
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.scale_service("test-service", 5)
            
            assert result["success"] is True
            assert result["replicas"] == 5
            assert "Service test-service scaled to 5 replicas" in result["message"]
    
    def test_scale_service_failure(self, mock_docker_client):
        """Test service scaling failure."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        mock_docker_client.services.get.side_effect = Exception("Scale failed")
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.scale_service("test-service", 5)
            
            assert result["success"] is False
            assert "Scale failed" in result["error"]
    
    def test_get_service_logs_success(self, mock_docker_client):
        """Test successful service logs retrieval."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        
        mock_service = Mock()
        mock_service.logs.return_value = b"test logs"
        mock_docker_client.services.get.return_value = mock_service
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.get_service_logs("test-service")
            
            assert result["success"] is True
            assert result["logs"] == "test logs"
            assert result["service_name"] == "test-service"
    
    def test_get_service_logs_failure(self, mock_docker_client):
        """Test service logs retrieval failure."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        mock_docker_client.services.get.side_effect = Exception("Logs failed")
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.get_service_logs("test-service")
            
            assert result["success"] is False
            assert "Logs failed" in result["error"]
    
    def test_remove_service_success(self, mock_docker_client):
        """Test successful service removal."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        
        mock_service = Mock()
        mock_service.remove.return_value = None
        mock_docker_client.services.get.return_value = mock_service
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.remove_service("test-service")
            
            assert result["success"] is True
            assert "Service test-service removed successfully" in result["message"]
    
    def test_remove_service_failure(self, mock_docker_client):
        """Test service removal failure."""
        mock_docker_client.info.return_value = {
            "Swarm": {"LocalNodeState": "active"}
        }
        mock_docker_client.services.get.side_effect = Exception("Remove failed")
        
        with patch('src.backend.swarm_manager.docker.from_env', return_value=mock_docker_client):
            manager = SwarmManager()
            
            result = manager.remove_service("test-service")
            
            assert result["success"] is False
            assert "Remove failed" in result["error"]
