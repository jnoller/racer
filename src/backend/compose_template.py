"""
Docker Compose template generator for conda-project deployments.
"""

import os
import yaml
from typing import Dict, List, Optional


def generate_compose_file(
    project_name: str,
    project_path: str,
    instances: int = 1,
    ports: Optional[Dict[str, int]] = None,
    environment: Optional[Dict[str, str]] = None,
    command: Optional[str] = None,
    custom_commands: Optional[List[str]] = None,
    use_load_balancer: bool = True,
) -> str:
    """
    Generate a Docker Compose file for a conda-project.

    Args:
        project_name: Name of the project/service
        project_path: Path to the conda-project directory
        instances: Number of instances to scale to
        ports: Port mappings (host_port: container_port)
        environment: Environment variables
        command: Override command to run
        custom_commands: Custom RUN commands for Dockerfile

    Returns:
        Docker Compose YAML content as string
    """

    # Default port mapping
    if ports is None:
        ports = {"8000": 8000}

    # Default environment
    if environment is None:
        environment = {}

    # Build context (project directory)
    build_context = project_path

    # Service configuration
    service_config = {
        "build": {"context": build_context, "dockerfile": "Dockerfile"},
        "environment": environment,
        "restart": "unless-stopped",
        "healthcheck": {
            "test": [
                "CMD",
                "curl",
                "-f",
                "http://localhost:8000/health",
                "||",
                "exit",
                "1",
            ],
            "interval": "30s",
            "timeout": "10s",
            "retries": "3",
            "start_period": "40s",
        },
    }

    # Add command override if specified
    if command:
        service_config["command"] = command

    # Handle port mapping and service creation
    if instances == 1:
        # For single instance, expose ports directly
        compose_ports = []
        for host_port, container_port in ports.items():
            # Remove /tcp suffix if present
            if isinstance(host_port, str) and host_port.endswith("/tcp"):
                host_port = host_port.replace("/tcp", "")
            if isinstance(container_port, str) and container_port.endswith("/tcp"):
                container_port = container_port.replace("/tcp", "")
            compose_ports.append(f"{host_port}:{container_port}")
        service_config["ports"] = compose_ports

        # Single service
        compose_data = {"services": {project_name: service_config}}

    elif instances > 1 and use_load_balancer:
        # For multiple instances, use load balancer approach
        nginx_config = generate_nginx_config(project_name, instances)

        # Create services for each instance
        services = {}
        for i in range(instances):
            instance_service = service_config.copy()
            instance_service["container_name"] = f"{project_name}_{i+1}"
            services[f"{project_name}_{i+1}"] = instance_service

        # Add nginx service
        base_port = list(ports.keys())[0] if ports else "8000"
        if isinstance(base_port, str) and base_port.endswith("/tcp"):
            base_port = base_port.replace("/tcp", "")

        services["nginx"] = {
            "image": "nginx:alpine",
            "ports": [f"{base_port}:8000"],
            "volumes": [f"./nginx.conf:/etc/nginx/nginx.conf:ro"],
            "depends_on": list(services.keys()),
            "restart": "unless-stopped",
        }

        # Write nginx config
        nginx_path = os.path.join(project_path, "nginx.conf")
        with open(nginx_path, "w") as f:
            f.write(nginx_config)

        compose_data = {"services": services}

    else:
        # For multiple instances without load balancer, create separate services
        services = {}

        if ports:
            base_port_key = list(ports.keys())[0]
            base_port_value = list(ports.values())[0]

            # Clean port values
            if isinstance(base_port_key, str) and base_port_key.endswith("/tcp"):
                base_port_key = base_port_key.replace("/tcp", "")
            if isinstance(base_port_value, str) and base_port_value.endswith("/tcp"):
                base_port_value = base_port_value.replace("/tcp", "")

            base_port = int(base_port_key)
            container_port = int(base_port_value)
        else:
            base_port = 8000
            container_port = 8000

        for i in range(instances):
            instance_service = service_config.copy()
            instance_service["container_name"] = f"{project_name}_{i+1}"
            instance_service["ports"] = [f"{base_port + i}:{container_port}"]
            services[f"{project_name}_{i+1}"] = instance_service

        compose_data = {"services": services}

    # Convert to YAML
    compose_yaml = yaml.dump(compose_data, default_flow_style=False, sort_keys=False)

    return compose_yaml


def write_compose_file(
    project_path: str, compose_content: str, filename: str = "docker-compose.yml"
) -> str:
    """
    Write a Docker Compose file to the project directory.

    Args:
        project_path: Path to the project directory
        compose_content: Docker Compose YAML content
        filename: Name of the compose file

    Returns:
        Path to the written compose file
    """
    compose_path = os.path.join(project_path, filename)

    with open(compose_path, "w") as f:
        f.write(compose_content)

    return compose_path


def generate_compose_with_networking(
    project_name: str,
    project_path: str,
    instances: int = 1,
    ports: Optional[Dict[str, int]] = None,
    environment: Optional[Dict[str, str]] = None,
    command: Optional[str] = None,
    custom_commands: Optional[List[str]] = None,
    load_balancer: bool = True,
) -> str:
    """
    Generate a Docker Compose file with networking and load balancer support.

    Args:
        project_name: Name of the project/service
        project_path: Path to the conda-project directory
        instances: Number of instances to scale to
        ports: Port mappings (host_port: container_port)
        environment: Environment variables
        command: Override command to run
        custom_commands: Custom RUN commands for Dockerfile
        load_balancer: Whether to include nginx load balancer

    Returns:
        Docker Compose YAML content as string
    """

    # Default port mapping
    if ports is None:
        ports = {"8000": 8000}

    # Default environment
    if environment is None:
        environment = {}

    # Convert ports to Docker Compose format
    compose_ports = []
    for host_port, container_port in ports.items():
        compose_ports.append(f"{host_port}:{container_port}")

    # Build context (project directory)
    build_context = project_path

    # Service configuration
    service_config = {
        "build": {"context": build_context, "dockerfile": "Dockerfile"},
        "environment": environment,
        "restart": "unless-stopped",
        "healthcheck": {
            "test": [
                "CMD",
                "curl",
                "-f",
                "http://localhost:8000/health",
                "||",
                "exit",
                "1",
            ],
            "interval": "30s",
            "timeout": "10s",
            "retries": "3",
            "start_period": "40s",
        },
    }

    # Add command override if specified
    if command:
        service_config["command"] = command

    # Compose file structure
    compose_data = {"version": "3.8", "services": {project_name: service_config}}

    # Add scaling configuration
    if instances > 1:
        compose_data["services"][project_name]["deploy"] = {"replicas": instances}

    # Add load balancer if requested
    if load_balancer and instances > 1:
        # Generate nginx configuration
        nginx_config = generate_nginx_config(project_name, instances)

        # Add nginx service
        compose_data["services"]["nginx"] = {
            "image": "nginx:alpine",
            "ports": compose_ports,
            "volumes": [f"./nginx.conf:/etc/nginx/nginx.conf:ro"],
            "depends_on": [project_name],
            "restart": "unless-stopped",
        }

        # Write nginx config
        nginx_path = os.path.join(project_path, "nginx.conf")
        with open(nginx_path, "w") as f:
            f.write(nginx_config)

    # Convert to YAML
    compose_yaml = yaml.dump(compose_data, default_flow_style=False, sort_keys=False)

    return compose_yaml


def generate_nginx_config(project_name: str, instances: int) -> str:
    """
    Generate nginx configuration for load balancing.

    Args:
        project_name: Name of the project service
        instances: Number of instances

    Returns:
        Nginx configuration content
    """

    # Generate upstream servers using Docker Compose service names
    upstream_servers = []
    for i in range(instances):
        # Docker Compose creates containers with pattern: {project_name}_{instance_number}
        upstream_servers.append(f"    server {project_name}_{i+1}:8000;")

    nginx_config = """events {
    worker_connections 1024;
}}

http {{
    resolver 127.0.0.11 valid=10s;
    
    upstream {project_name}_backend {{
{upstream_block}
    }}
    
    server {{
        listen 8000;
        
        location / {{
            proxy_pass http://{project_name}_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
        
        location /health {{
            proxy_pass http://{project_name}_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }}
    }}
}}"""

    return nginx_config
