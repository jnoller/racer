"""
Unit tests for API client (fixed version).
"""

import pytest
import requests
from unittest.mock import Mock, patch
from src.client.api import RacerAPIClient, RacerAPIError


class TestRacerAPIClient:
    """Test cases for RacerAPIClient class."""
    
    def test_init_default(self):
        """Test client initialization with default values."""
        client = RacerAPIClient()
        assert client.base_url == "http://localhost:8001"
        assert client.timeout == 30
        assert client.session is not None
    
    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = RacerAPIClient(base_url="http://test:9000", timeout=60)
        assert client.base_url == "http://test:9000"
        assert client.timeout == 60
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_health_success(self, mock_make_request):
        """Test successful health check."""
        mock_make_request.return_value = {
            "status": "healthy",
            "timestamp": "2023-01-01T00:00:00",
            "version": "0.1.0",
            "service": "racer-api"
        }
        
        client = RacerAPIClient()
        result = client.health()
        
        assert result["status"] == "healthy"
        assert result["version"] == "0.1.0"
        mock_make_request.assert_called_once_with('GET', '/health')
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_health_http_error(self, mock_make_request):
        """Test health check with HTTP error."""
        mock_make_request.side_effect = RacerAPIError("HTTP error 500: Server Error")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="HTTP error 500"):
            client.health()
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_health_connection_error(self, mock_make_request):
        """Test health check with connection error."""
        mock_make_request.side_effect = RacerAPIError("Connection error: Connection failed")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="Connection error"):
            client.health()
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_liveness_success(self, mock_make_request):
        """Test successful liveness check."""
        mock_make_request.return_value = {
            "alive": True,
            "uptime": "1h 30m",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        client = RacerAPIClient()
        result = client.liveness()
        
        assert result["alive"] is True
        assert result["uptime"] == "1h 30m"
        mock_make_request.assert_called_once_with('GET', '/liveness')
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_readiness_success(self, mock_make_request):
        """Test successful readiness check."""
        mock_make_request.return_value = {
            "ready": True,
            "checks": {
                "docker": "ok",
                "database": "ok"
            },
            "timestamp": "2023-01-01T00:00:00"
        }
        
        client = RacerAPIClient()
        result = client.readiness()
        
        assert result["ready"] is True
        assert result["checks"]["docker"] == "ok"
        mock_make_request.assert_called_once_with('GET', '/ready')
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_info_success(self, mock_make_request):
        """Test successful info retrieval."""
        mock_make_request.return_value = {
            "message": "Racer API Server",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health"
        }
        
        client = RacerAPIClient()
        result = client.info()
        
        assert result["message"] == "Racer API Server"
        assert result["version"] == "0.1.0"
        mock_make_request.assert_called_once_with('GET', '/')
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_make_request_post_success(self, mock_make_request):
        """Test successful POST request."""
        mock_make_request.return_value = {"success": True, "data": "test"}
        
        client = RacerAPIClient()
        result = client._make_request('POST', '/test', json={"key": "value"})
        
        assert result["success"] is True
        assert result["data"] == "test"
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_make_request_get_success(self, mock_make_request):
        """Test successful GET request."""
        mock_make_request.return_value = {"success": True, "data": "test"}
        
        client = RacerAPIClient()
        result = client._make_request('GET', '/test')
        
        assert result["success"] is True
        assert result["data"] == "test"
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_make_request_http_error(self, mock_make_request):
        """Test POST request with HTTP error."""
        mock_make_request.side_effect = RacerAPIError("HTTP error 400: Bad Request")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="HTTP error 400"):
            client._make_request('POST', '/test', json={"key": "value"})
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_make_request_timeout(self, mock_make_request):
        """Test GET request with timeout."""
        mock_make_request.side_effect = RacerAPIError("Request to http://localhost:8001/test timed out after 30 seconds")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="timed out"):
            client._make_request('GET', '/test')
    
    @patch('src.client.api.RacerAPIClient._make_request')
    def test_make_request_json_decode_error(self, mock_make_request):
        """Test POST request with JSON decode error."""
        mock_make_request.side_effect = RacerAPIError("Invalid JSON response")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="Invalid JSON response"):
            client._make_request('POST', '/test', json={"key": "value"})
    
    def test_racer_api_error_str(self):
        """Test RacerAPIError string representation."""
        error = RacerAPIError("Test error message")
        assert str(error) == "Test error message"
    
    def test_racer_api_error_with_details(self):
        """Test RacerAPIError with details."""
        error = RacerAPIError("Test error")
        assert str(error) == "Test error"
