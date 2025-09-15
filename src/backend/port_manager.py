"""
Port management utilities for Racer.

This module provides utilities for managing port assignments and avoiding conflicts.
"""

import socket
import random
from typing import Optional, List


def find_available_port(start_port: int = 8000, end_port: int = 9000) -> int:
    """
    Find an available port in the specified range.
    
    Args:
        start_port: Starting port number (inclusive)
        end_port: Ending port number (exclusive)
        
    Returns:
        Available port number
        
    Raises:
        RuntimeError: If no available port is found in the range
    """
    for port in range(start_port, end_port):
        if is_port_available(port):
            return port
    
    raise RuntimeError(f"No available ports found in range {start_port}-{end_port-1}")


def find_available_ports(count: int, start_port: int = 8000, end_port: int = 9000) -> List[int]:
    """
    Find multiple available ports in the specified range.
    
    Args:
        count: Number of ports to find
        start_port: Starting port number (inclusive)
        end_port: Ending port number (exclusive)
        
    Returns:
        List of available port numbers
        
    Raises:
        RuntimeError: If not enough available ports are found
    """
    ports = []
    for port in range(start_port, end_port):
        if is_port_available(port):
            ports.append(port)
            if len(ports) >= count:
                return ports
    
    raise RuntimeError(f"Only found {len(ports)} available ports, need {count}")


def is_port_available(port: int) -> bool:
    """
    Check if a port is available.
    
    Args:
        port: Port number to check
        
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False


def get_random_port(start_port: int = 8000, end_port: int = 9000) -> int:
    """
    Get a random available port in the specified range.
    
    Args:
        start_port: Starting port number (inclusive)
        end_port: Ending port number (exclusive)
        
    Returns:
        Random available port number
        
    Raises:
        RuntimeError: If no available port is found after multiple attempts
    """
    max_attempts = 100
    for _ in range(max_attempts):
        port = random.randint(start_port, end_port - 1)
        if is_port_available(port):
            return port
    
    # Fallback to sequential search
    return find_available_port(start_port, end_port)


def get_service_port_range() -> tuple[int, int]:
    """
    Get the recommended port range for user services.
    
    Returns:
        Tuple of (start_port, end_port) for service ports
    """
    return (8000, 9000)


def get_api_port() -> int:
    """
    Get the recommended port for the API server.
    
    Returns:
        Port number for the API server
    """
    return 8001


def get_management_port() -> int:
    """
    Get the recommended port for management services.
    
    Returns:
        Port number for management services
    """
    return 8002
