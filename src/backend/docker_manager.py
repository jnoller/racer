"""
Docker container management for conda-project deployments.
"""

import docker
import os
import time
import uuid
from typing import Dict, Any, List
from datetime import datetime
import threading
import queue


class ContainerManager:
    """Manages Docker containers for conda-project deployments."""

    def __init__(self, db_manager=None):
        """Initialize the Docker manager."""
        try:
            self.client = docker.from_env()
            self.client.ping()  # Test connection
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Docker: {e}")

        self.db_manager = db_manager
        self.running_containers = {}  # Keep for backward compatibility
        self.container_logs = {}

    def build_image(
        self,
        project_path: str,
        project_name: str,
        dockerfile_path: str,
        custom_commands: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a Docker image for a conda-project.

        Args:
            project_path: Path to the project directory
            project_name: Name for the Docker image
            dockerfile_path: Path to the Dockerfile
            custom_commands: Optional custom RUN commands

        Returns:
            Dictionary with build results
        """
        try:
            # Generate Dockerfile if it doesn't exist
            from dockerfile_template import write_dockerfile

            if not os.path.exists(dockerfile_path):
                write_dockerfile(project_path, dockerfile_path, custom_commands)

            # Build the image using Docker SDK
            image, build_logs = self.client.images.build(
                path=project_path,
                dockerfile=dockerfile_path,
                tag=project_name,
                rm=True,
                forcerm=True,
            )

            return {
                "success": True,
                "image_id": image.id,
                "image_tag": project_name,
                "message": f"Successfully built image {project_name}",
                "build_logs": [log for log in build_logs],
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to build image {project_name}: {e}",
            }

    def run_container(
        self,
        project_name: str,
        ports: Dict[str, int] = None,
        environment: Dict[str, str] = None,
        command: str = None,
    ) -> Dict[str, Any]:
        """
        Run a Docker container for a conda-project.

        Args:
            project_name: Name/tag of the Docker image
            ports: Port mappings (host_port: container_port)
            environment: Environment variables
            command: Override command to run

        Returns:
            Dictionary with container run results
        """
        try:
            # Default port mapping
            if ports is None:
                ports = {"8000/tcp": 8000}

            # Default environment
            if environment is None:
                environment = {}

            # Generate unique container name
            container_name = (
                f"{project_name}-{int(time.time())}-{str(uuid.uuid4())[:8]}"
            )

            # Run the container using Docker SDK
            container = self.client.containers.run(
                project_name,
                command=command,
                ports=ports,
                environment=environment,
                detach=True,
                remove=False,
                name=container_name,
            )

            # Store container info
            container_id = container.id
            self.running_containers[container_id] = {
                "container": container,
                "container_name": container_name,
                "project_name": project_name,
                "ports": ports,
                "environment": environment,
                "started_at": datetime.now().isoformat(),
                "status": "running",
            }

            # Store in database if available
            if self.db_manager:
                # Create or get project
                project = self.db_manager.get_project(name=project_name)
                if not project:
                    project = self.db_manager.create_project(
                        name=project_name, image_name=project_name
                    )

                if project:
                    # Create container record
                    self.db_manager.create_container(
                        container_id=container_id,
                        container_name=container_name,
                        project_id=project.id,
                        status="running",
                        ports=ports,
                        environment=environment,
                        command=command,
                    )

            # Start log collection in background
            self._start_log_collection(container_id)

            return {
                "success": True,
                "container_id": container_id,
                "container_name": container_name,
                "ports": ports,
                "message": f"Successfully started container {container_name}",
                "status": "running",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to run container {project_name}: {e}",
            }

    def stop_container(self, container_id: str) -> Dict[str, Any]:
        """
        Stop a running container.

        Args:
            container_id: ID of the container to stop

        Returns:
            Dictionary with stop results
        """
        try:
            # Check if container exists in Docker
            try:
                container = self.client.containers.get(container_id)
            except Exception:
                return {
                    "success": False,
                    "error": "Container not found",
                    "message": f"Container {container_id} not found in Docker",
                }

            if container_id not in self.running_containers:
                # Container exists in Docker but not tracked - add it to tracking
                self.running_containers[container_id] = {
                    "container": container,
                    "container_name": container.name,
                    "status": container.status,
                    "started_at": container.attrs.get("State", {}).get(
                        "StartedAt", "unknown"
                    ),
                }

            container_info = self.running_containers[container_id]
            container = container_info["container"]
            container_name = container_info["container_name"]

            # Stop the container
            container.stop(timeout=10)

            # Update status
            container_info["status"] = "stopped"
            container_info["stopped_at"] = datetime.now().isoformat()

            # Update database if available
            if self.db_manager:
                self.db_manager.update_container_status(container_id, "stopped")

            return {
                "success": True,
                "container_id": container_id,
                "message": f"Successfully stopped container {container_name}",
                "status": "stopped",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to stop container {container_id}: {e}",
            }

    def remove_container(self, container_id: str) -> Dict[str, Any]:
        """
        Remove a container.

        Args:
            container_id: ID of the container to remove

        Returns:
            Dictionary with removal results
        """
        try:
            # Check if container exists in Docker
            try:
                container = self.client.containers.get(container_id)
            except Exception:
                return {
                    "success": False,
                    "error": "Container not found",
                    "message": f"Container {container_id} not found in Docker",
                }

            if container_id not in self.running_containers:
                # Container exists in Docker but not tracked - add it to tracking
                self.running_containers[container_id] = {
                    "container": container,
                    "container_name": container.name,
                    "status": container.status,
                    "started_at": container.attrs.get("State", {}).get(
                        "StartedAt", "unknown"
                    ),
                }

            container_info = self.running_containers[container_id]
            container = container_info["container"]
            container_name = container_info["container_name"]

            # Remove the container
            container.remove(force=True)

            # Remove from tracking
            del self.running_containers[container_id]
            if container_id in self.container_logs:
                del self.container_logs[container_id]

            # Remove from database if available
            if self.db_manager:
                self.db_manager.delete_container(container_id)

            return {
                "success": True,
                "container_id": container_id,
                "message": f"Successfully removed container {container_name}",
                "status": "removed",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to remove container {container_id}: {e}",
            }

    def get_container_status(self, container_id: str) -> Dict[str, Any]:
        """
        Get the status of a container.

        Args:
            container_id: ID of the container

        Returns:
            Dictionary with container status
        """
        try:
            # First check if it's a tracked container
            if container_id in self.running_containers:
                container_info = self.running_containers[container_id]
                container = container_info["container"]
                ports = container_info["ports"]
            else:
                # Try to get container directly from Docker (for Docker Compose managed containers)
                try:
                    container = self.client.containers.get(container_id)
                    # For Docker Compose containers, we need to extract ports from container info
                    ports = {}
                    if container.attrs.get("NetworkSettings", {}).get("Ports"):
                        for container_port, host_bindings in container.attrs["NetworkSettings"]["Ports"].items():
                            if host_bindings:
                                for binding in host_bindings:
                                    host_port = binding.get("HostPort", "")
                                    if host_port:
                                        ports[f"{host_port}/tcp"] = int(container_port.split("/")[0])
                except Exception as e:
                    return {
                        "success": False,
                        "error": "Container not found",
                        "message": f"Container {container_id} not found: {str(e)}",
                    }

            # Refresh container info
            container.reload()

            # Get additional info based on container type
            if container_id in self.running_containers:
                container_info = self.running_containers[container_id]
                environment = container_info["environment"]
                started_at = container_info["started_at"]
                stopped_at = container_info.get("stopped_at")
            else:
                # For Docker Compose containers, use default values
                environment = {}
                started_at = ""
                stopped_at = None

            return {
                "success": True,
                "container_id": container_id,
                "container_name": container.name,
                "status": container.status,
                "ports": ports,
                "environment": environment,
                "started_at": started_at,
                "stopped_at": stopped_at,
                "image": container.image.tags[0]
                if container.image.tags
                else container.image.id,
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get status for container {container_id}: {e}",
            }

    def get_container_logs(self, container_id: str, tail: int = 100) -> Dict[str, Any]:
        """
        Get logs from a container.

        Args:
            container_id: ID of the container
            tail: Number of lines to return

        Returns:
            Dictionary with container logs
        """
        try:
            if container_id not in self.running_containers:
                return {
                    "success": False,
                    "error": "Container not found",
                    "message": f"Container {container_id} not found",
                }

            container_info = self.running_containers[container_id]
            container = container_info["container"]
            container_name = container_info["container_name"]

            # Get logs
            logs = container.logs(tail=tail, timestamps=True).decode("utf-8")

            return {
                "success": True,
                "container_id": container_id,
                "logs": logs,
                "message": f"Retrieved logs for container {container_name}",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get logs for container {container_id}: {e}",
            }

    def list_containers(self) -> Dict[str, Any]:
        """
        List all tracked containers.

        Returns:
            Dictionary with container list
        """
        try:
            containers = []
            for container_id, info in self.running_containers.items():
                container = info["container"]
                container.reload()  # Refresh status

                containers.append(
                    {
                        "container_id": container_id,
                        "container_name": container.name,
                        "project_name": info["project_name"],
                        "status": container.status,
                        "ports": info["ports"],
                        "started_at": info["started_at"],
                        "stopped_at": info.get("stopped_at"),
                        "image": container.image.tags[0]
                        if container.image.tags
                        else container.image.id,
                    }
                )

            return {
                "success": True,
                "containers": containers,
                "count": len(containers),
                "message": f"Found {len(containers)} tracked containers",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list containers: {e}",
            }

    def _start_log_collection(self, container_id: str):
        """Start collecting logs for a container in the background."""

        def collect_logs():
            try:
                container_info = self.running_containers[container_id]
                container = container_info["container"]

                # Initialize log storage
                if container_id not in self.container_logs:
                    self.container_logs[container_id] = queue.Queue()

                # Stream logs
                for line in container.logs(stream=True, follow=True, timestamps=True):
                    self.container_logs[container_id].put(line.decode("utf-8"))

            except Exception as e:
                print(f"Error collecting logs for container {container_id}: {e}")

        # Start log collection thread
        log_thread = threading.Thread(target=collect_logs, daemon=True)
        log_thread.start()

    def cleanup_stopped_containers(self):
        """Clean up stopped containers."""
        try:
            stopped_containers = []
            for container_id, info in self.running_containers.items():
                container = info["container"]
                container.reload()

                if container.status in ["exited", "dead"]:
                    stopped_containers.append(container_id)

            for container_id in stopped_containers:
                self.remove_container(container_id)

            return {
                "success": True,
                "cleaned_up": len(stopped_containers),
                "message": f"Cleaned up {len(stopped_containers)} stopped containers",
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to cleanup containers: {e}",
            }
