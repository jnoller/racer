"""
Unit tests for API client.
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
        assert client.base_url == "http://localhost:8000"
        assert client.timeout == 30
        assert client.session is not None
    
    def test_init_custom(self):
        """Test client initialization with custom values."""
        client = RacerAPIClient(base_url="http://test:9000", timeout=60)
        assert client.base_url == "http://test:9000"
        assert client.timeout == 60
    
    @patch('requests.Session.get')
    def test_health_success(self, mock_get):
        """Test successful health check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "healthy",
            "timestamp": "2023-01-01T00:00:00",
            "version": "0.1.0",
            "service": "racer-api"
        }
        mock_get.return_value = mock_response
        
        client = RacerAPIClient()
        result = client.health()
        
        assert result["status"] == "healthy"
        assert result["version"] == "0.1.0"
        mock_get.assert_called_once_with("http://localhost:8000/health", timeout=30)
    
    @patch('requests.Session.get')
    def test_health_http_error(self, mock_get):
        """Test health check with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("Server Error")
        mock_get.return_value = mock_response
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="HTTP error 500"):
            client.health()
    
    @patch('requests.Session.get')
    def test_health_connection_error(self, mock_get):
        """Test health check with connection error."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="Connection error"):
            client.health()
    
    @patch('requests.Session.get')
    def test_liveness_success(self, mock_get):
        """Test successful liveness check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "alive": True,
            "uptime": "1h 30m",
            "timestamp": "2023-01-01T00:00:00"
        }
        mock_get.return_value = mock_response
        
        client = RacerAPIClient()
        result = client.liveness()
        
        assert result["alive"] is True
        assert result["uptime"] == "1h 30m"
        mock_get.assert_called_once_with("http://localhost:8000/liveness", timeout=30)
    
    @patch('requests.Session.get')
    def test_readiness_success(self, mock_get):
        """Test successful readiness check."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "ready": True,
            "checks": {
                "docker": "ok",
                "database": "ok"
            },
            "timestamp": "2023-01-01T00:00:00"
        }
        mock_get.return_value = mock_response
        
        client = RacerAPIClient()
        result = client.readiness()
        
        assert result["ready"] is True
        assert result["checks"]["docker"] == "ok"
        mock_get.assert_called_once_with("http://localhost:8000/ready", timeout=30)
    
    @patch('requests.Session.get')
    def test_info_success(self, mock_get):
        """Test successful info retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": "Racer API Server",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health"
        }
        mock_get.return_value = mock_response
        
        client = RacerAPIClient()
        result = client.info()
        
        assert result["message"] == "Racer API Server"
        assert result["version"] == "0.1.0"
        mock_get.assert_called_once_with("http://localhost:8000/", timeout=30)
    
    @patch('requests.Session.post')
    def test_make_request_post_success(self, mock_post):
        """Test successful POST request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_post.return_value = mock_response
        
        client = RacerAPIClient()
        result = client._make_request('POST', '/test', json={"key": "value"})
        
        assert result["success"] is True
        assert result["data"] == "test"
        mock_post.assert_called_once_with(
            "http://localhost:8000/test",
            json={"key": "value"},
            timeout=30
        )
    
    @patch('requests.Session.get')
    def test_make_request_get_success(self, mock_get):
        """Test successful GET request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_get.return_value = mock_response
        
        client = RacerAPIClient()
        result = client._make_request('GET', '/test')
        
        assert result["success"] is True
        assert result["data"] == "test"
        mock_get.assert_called_once_with("http://localhost:8000/test", timeout=30)
    
    @patch('requests.Session.post')
    def test_make_request_http_error(self, mock_post):
        """Test POST request with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Client Error")
        mock_post.return_value = mock_response
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="HTTP error 400"):
            client._make_request('POST', '/test', json={"key": "value"})
    
    @patch('requests.Session.get')
    def test_make_request_timeout(self, mock_get):
        """Test GET request with timeout."""
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="Request timeout"):
            client._make_request('GET', '/test')
    
    @patch('requests.Session.post')
    def test_make_request_json_decode_error(self, mock_post):
        """Test POST request with JSON decode error."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response
        
        client = RacerAPIClient()
        
        with pytest.raises(RacerAPIError, match="Invalid JSON response"):
            client._make_request('POST', '/test', json={"key": "value"})
    
    def test_racer_api_error_str(self):
        """Test RacerAPIError string representation."""
        error = RacerAPIError("Test error message")
        assert str(error) == "Test error message"
    
    def test_racer_api_error_with_details(self):
        """Test RacerAPIError with details."""
        error = RacerAPIError("Test error", details={"code": 500, "message": "Server error"})
        assert str(error) == "Test error"
        assert error.details == {"code": 500, "message": "Server error"}
