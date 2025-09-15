"""
API client for communicating with the Racer backend server.
"""

import requests
import json
from typing import Dict, Any
from urllib.parse import urljoin


class RacerAPIError(Exception):
    """Custom exception for API-related errors."""

    pass


class RacerAPIClient:
    """Client for interacting with the Racer API server."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
        verbose: bool = False,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the Racer API server
            timeout: Request timeout in seconds
            verbose: Enable verbose output
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()

        # Set default headers
        self.session.headers.update(
            {"Content-Type": "application/json", "User-Agent": "racerctl/0.1.0"}
        )

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a request to the API server.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., '/health')
            **kwargs: Additional arguments for requests

        Returns:
            JSON response as dictionary

        Raises:
            RacerAPIError: If the request fails
        """
        url = urljoin(self.base_url, endpoint)

        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()

            # Try to parse JSON response
            try:
                return response.json()
            except json.JSONDecodeError:
                return {"message": response.text}

        except requests.exceptions.ConnectionError:
            raise RacerAPIError(f"Could not connect to Racer API at {self.base_url}")
        except requests.exceptions.Timeout:
            raise RacerAPIError(
                f"Request to {url} timed out after {self.timeout} seconds"
            )
        except requests.exceptions.HTTPError as e:
            raise RacerAPIError(
                f"HTTP error {e.response.status_code}: {e.response.text}"
            )
        except requests.exceptions.RequestException as e:
            raise RacerAPIError(f"Request failed: {str(e)}")

    def health(self) -> Dict[str, Any]:
        """
        Get health status from the API server.

        Returns:
            Health status information
        """
        return self._make_request("GET", "/health")

    def liveness(self) -> Dict[str, Any]:
        """
        Get liveness status from the API server.

        Returns:
            Liveness status information
        """
        return self._make_request("GET", "/liveness")

    def readiness(self) -> Dict[str, Any]:
        """
        Get readiness status from the API server.

        Returns:
            Readiness status information
        """
        return self._make_request("GET", "/ready")

    def info(self) -> Dict[str, Any]:
        """
        Get basic API information.

        Returns:
            API information
        """
        return self._make_request("GET", "/")
