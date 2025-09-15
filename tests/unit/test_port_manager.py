"""
Unit tests for port management functionality.
"""

import pytest
import socket
from unittest.mock import patch, Mock
from src.backend.port_manager import (
    find_available_port,
    find_available_ports,
    is_port_available,
    get_random_port,
    get_service_port_range,
    get_api_port,
    get_management_port
)


class TestPortManager:
    """Test cases for port management utilities."""
    
    def test_is_port_available_true(self):
        """Test port availability check when port is available."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.bind.return_value = None
            result = is_port_available(8080)
            assert result is True
    
    def test_is_port_available_false(self):
        """Test port availability check when port is in use."""
        with patch('socket.socket') as mock_socket:
            mock_socket.return_value.__enter__.return_value.bind.side_effect = OSError("Address already in use")
            result = is_port_available(8080)
            assert result is False
    
    def test_find_available_port_success(self):
        """Test finding an available port."""
        with patch('src.backend.port_manager.is_port_available') as mock_check:
            mock_check.side_effect = [False, False, True]  # First two ports busy, third available
            result = find_available_port(8080, 8083)
            assert result == 8082
            assert mock_check.call_count == 3
    
    def test_find_available_port_no_ports(self):
        """Test finding available port when none are available."""
        with patch('src.backend.port_manager.is_port_available', return_value=False):
            with pytest.raises(RuntimeError, match="No available ports found"):
                find_available_port(8080, 8081)
    
    def test_find_available_ports_success(self):
        """Test finding multiple available ports."""
        with patch('src.backend.port_manager.is_port_available') as mock_check:
            mock_check.side_effect = [True, False, True, True]  # 3 available ports
            result = find_available_ports(3, 8080, 8084)
            assert result == [8080, 8082, 8083]
            assert mock_check.call_count == 4
    
    def test_find_available_ports_insufficient(self):
        """Test finding multiple ports when insufficient are available."""
        with patch('src.backend.port_manager.is_port_available', return_value=False):
            with pytest.raises(RuntimeError, match="Only found 0 available ports, need 3"):
                find_available_ports(3, 8080, 8081)
    
    def test_get_random_port_success(self):
        """Test getting a random available port."""
        with patch('src.backend.port_manager.is_port_available') as mock_check:
            mock_check.side_effect = [False, True]  # First random port busy, second available
            with patch('random.randint', return_value=8085):
                result = get_random_port(8080, 8090)
                assert result == 8085
                assert mock_check.call_count == 2
    
    def test_get_random_port_fallback(self):
        """Test random port fallback to sequential search."""
        with patch('src.backend.port_manager.is_port_available', return_value=False):
            with patch('src.backend.port_manager.find_available_port', return_value=9000) as mock_find:
                result = get_random_port(8080, 8090)
                assert result == 9000
                mock_find.assert_called_once_with(8080, 8090)
    
    def test_get_service_port_range(self):
        """Test getting service port range."""
        start, end = get_service_port_range()
        assert start == 8000
        assert end == 9000
    
    def test_get_api_port(self):
        """Test getting API port."""
        port = get_api_port()
        assert port == 8001
    
    def test_get_management_port(self):
        """Test getting management port."""
        port = get_management_port()
        assert port == 8002
    
    def test_port_ranges_non_overlapping(self):
        """Test that different port ranges don't overlap."""
        api_port = get_api_port()
        mgmt_port = get_management_port()
        service_start, service_end = get_service_port_range()
        
        # API port should be within service range (8001 is in 8000-9000)
        assert service_start <= api_port < service_end
        
        # Management port should be within service range (8002 is in 8000-9000)
        assert service_start <= mgmt_port < service_end
        
        # API and management ports should be different
        assert api_port != mgmt_port
        
        # Both ports should be in the service range
        assert api_port >= service_start and api_port < service_end
        assert mgmt_port >= service_start and mgmt_port < service_end
