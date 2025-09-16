"""
Docker Swarm management for Racer deployment system.
Handles service creation, scaling, and management using Docker Swarm.
"""

import docker
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class SwarmManager:
    """
    Manages Docker Swarm services for project scaling and deployment.
    """

    def __init__(self, db_manager=None):
        """
        Initialize the SwarmManager.

        Args:
            db_manager: Database manager instance for persistence
        """
        self.client = docker.from_env()
        self.db_manager = db_manager
        self.swarm_initialized = False
        self._check_swarm_mode()

    def _check_swarm_mode(self) -> bool:
        """
        Check if Docker is in swarm mode.

        Returns:
            True if swarm mode is active, False otherwise
        """
        try:
            info = self.client.info()
            self.swarm_initialized = (
                info.get("Swarm", {}).get("LocalNodeState") == "active"
            )
            return self.swarm_initialized
        except Exception as e:
            logger.error(f"Failed to check swarm mode: {e}")
            self.swarm_initialized = False
            return False

    def init_swarm(self, advertise_addr: str = "127.0.0.1") -> Dict[str, Any]:
        """
        Initialize Docker Swarm mode.

        Args:
            advertise_addr: Address to advertise for swarm

        Returns:
            Dictionary with initialization result
        """
        try:
            if self.swarm_initialized:
                return {
                    "success": True,
                    "message": "Swarm already initialized",
                    "swarm_id": self.client.info()["Swarm"]["Cluster"]["ID"],
                }

            # Initialize swarm
            result = self.client.swarm.init(
                advertise_addr=advertise_addr,
                listen_addr="0.0.0.0:2377",
                force_new_cluster=False,
            )

            self.swarm_initialized = True
            return {
                "success": True,
                "message": "Swarm initialized successfully",
                "swarm_id": result,
            }
        except Exception as e:
            logger.error(f"Failed to initialize swarm: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to initialize swarm: {str(e)}",
            }

    def create_service(
        self,
        service_name: str,
        image: str,
        replicas: int = 1,
        ports: Optional[Dict[str, int]] = None,
        environment: Optional[Dict[str, str]] = None,
        command: Optional[List[str]] = None,
        healthcheck: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a Docker Swarm service.

        Args:
            service_name: Name of the service
            image: Docker image to use
            replicas: Number of replicas to run
            ports: Port mappings (container_port: host_port)
            environment: Environment variables
            command: Command to run in the container
            healthcheck: Health check configuration

        Returns:
            Dictionary with service creation result
        """
        try:
            if not self.swarm_initialized:
                init_result = self.init_swarm()
                if not init_result["success"]:
                    return init_result

            # Prepare service specification
            service_spec = {
                "name": service_name,
                "image": image,
                "replicas": replicas,
                "restart_policy": {
                    "condition": "on-failure",
                    "delay": 5,
                    "max_attempts": 3,
                },
            }

            # Add port mappings if provided
            if ports:
                endpoint_spec = {"ports": []}
                for container_port, host_port in ports.items():
                    endpoint_spec["ports"].append(
                        {
                            "target_port": int(container_port.split("/")[0]),
                            "published_port": host_port,
                            "protocol": "tcp",
                        }
                    )
                service_spec["endpoint_spec"] = endpoint_spec

            # Add environment variables
            if environment:
                service_spec["env"] = [f"{k}={v}" for k, v in environment.items()]

            # Add command
            if command:
                service_spec["command"] = command

            # Add health check
            if healthcheck:
                service_spec["healthcheck"] = healthcheck
            else:
                # Default health check for conda projects
                service_spec["healthcheck"] = {
                    "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                    "interval": 30,
                    "timeout": 10,
                    "retries": 3,
                    "start_period": 60,
                }

            # Create the service using proper Docker SDK parameters
            service = self.client.services.create(
                image=image,
                name=service_name,
                command=command,
                env=environment,
                mode=docker.types.ServiceMode("replicated", replicas=replicas),
                restart_policy=docker.types.RestartPolicy(
                    condition="on-failure", delay=5, max_attempts=3
                ),
                healthcheck=docker.types.Healthcheck(
                    test=["CMD", "curl", "-f", "http://localhost:8000/health"],
                    interval=30 * 10**9,  # 30 seconds in nanoseconds
                    timeout=10 * 10**9,  # 10 seconds in nanoseconds
                    retries=3,
                    start_period=60 * 10**9,  # 60 seconds in nanoseconds
                )
                if not healthcheck
                else docker.types.Healthcheck(**healthcheck),
            )

            # Store in database if available
            if self.db_manager:
                try:
                    self.db_manager.create_scale_group(
                        name=service_name,
                        service_id=service.id,
                        replicas=replicas,
                        image=image,
                        ports=ports or {},
                        environment=environment or {},
                    )
                except Exception as e:
                    logger.warning(f"Failed to store service in database: {e}")

            return {
                "success": True,
                "service_id": service.id,
                "service_name": service_name,
                "replicas": replicas,
                "message": f"Service {service_name} created successfully with {replicas} replicas",
            }

        except Exception as e:
            logger.error(f"Failed to create service {service_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create service {service_name}: {str(e)}",
            }

    def scale_service(self, service_name: str, replicas: int) -> Dict[str, Any]:
        """
        Scale a Docker Swarm service to the specified number of replicas.

        Args:
            service_name: Name of the service to scale
            replicas: Target number of replicas

        Returns:
            Dictionary with scaling result
        """
        try:
            if not self.swarm_initialized:
                return {
                    "success": False,
                    "error": "Swarm not initialized",
                    "message": "Docker Swarm is not initialized",
                }

            # Get the service
            service = self.client.services.get(service_name)

            # Scale the service
            service.scale(replicas)

            # Update database if available
            if self.db_manager:
                try:
                    scale_group = self.db_manager.get_scale_group_by_name(service_name)
                    if scale_group:
                        self.db_manager.update_scale_group(
                            scale_group.id, replicas=replicas
                        )
                except Exception as e:
                    logger.warning(f"Failed to update scale group in database: {e}")

            return {
                "success": True,
                "service_name": service_name,
                "replicas": replicas,
                "message": f"Service {service_name} scaled to {replicas} replicas",
            }

        except docker.errors.NotFound:
            return {
                "success": False,
                "error": "Service not found",
                "message": f"Service {service_name} not found",
            }
        except Exception as e:
            logger.error(f"Failed to scale service {service_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to scale service {service_name}: {str(e)}",
            }

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """
        Get the status of a Docker Swarm service.

        Args:
            service_name: Name of the service

        Returns:
            Dictionary with service status information
        """
        try:
            if not self.swarm_initialized:
                return {
                    "success": False,
                    "error": "Swarm not initialized",
                    "message": "Docker Swarm is not initialized",
                }

            service = self.client.services.get(service_name)
            service.reload()

            # Get service tasks (replicas)
            tasks = service.tasks()

            # Count running tasks
            running_tasks = [
                task for task in tasks if task["Status"]["State"] == "running"
            ]
            total_tasks = len(tasks)

            # Get service ports
            ports = {}
            if service.attrs.get("Endpoint", {}).get("Ports"):
                for port in service.attrs["Endpoint"]["Ports"]:
                    ports[f"{port['TargetPort']}/tcp"] = port["PublishedPort"]

            return {
                "success": True,
                "service_name": service_name,
                "service_id": service.id,
                "replicas": service.attrs["Spec"]["Mode"]["Replicated"]["Replicas"],
                "running_replicas": len(running_tasks),
                "total_tasks": total_tasks,
                "status": "running" if len(running_tasks) > 0 else "stopped",
                "ports": ports,
                "image": service.attrs["Spec"]["TaskTemplate"]["ContainerSpec"][
                    "Image"
                ],
                "created_at": service.attrs["CreatedAt"],
                "updated_at": service.attrs["UpdatedAt"],
            }

        except docker.errors.NotFound:
            return {
                "success": False,
                "error": "Service not found",
                "message": f"Service {service_name} not found",
            }
        except Exception as e:
            logger.error(f"Failed to get service status for {service_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get service status for {service_name}: {str(e)}",
            }

    def list_services(self) -> Dict[str, Any]:
        """
        List all Docker Swarm services.

        Returns:
            Dictionary with list of services
        """
        try:
            if not self.swarm_initialized:
                return {
                    "success": False,
                    "error": "Swarm not initialized",
                    "message": "Docker Swarm is not initialized",
                    "services": [],
                }

            services = self.client.services.list()
            service_list = []

            for service in services:
                try:
                    service.reload()
                    tasks = service.tasks()
                    running_tasks = [
                        task for task in tasks if task["Status"]["State"] == "running"
                    ]

                    # Get service ports
                    ports = {}
                    if service.attrs.get("Endpoint", {}).get("Ports"):
                        for port in service.attrs["Endpoint"]["Ports"]:
                            ports[f"{port['TargetPort']}/tcp"] = port["PublishedPort"]

                    service_info = {
                        "name": service.name,  # Use 'name' instead of 'service_name' for consistency
                        "service_name": service.name,
                        "service_id": service.id,
                        "replicas": service.attrs["Spec"]["Mode"]["Replicated"][
                            "Replicas"
                        ],
                        "instances": service.attrs["Spec"]["Mode"]["Replicated"][
                            "Replicas"
                        ],  # Add instances field for compatibility
                        "running_replicas": len(running_tasks),
                        "status": "running" if len(running_tasks) > 0 else "stopped",
                        "ports": ports,
                        "image": service.attrs["Spec"]["TaskTemplate"]["ContainerSpec"][
                            "Image"
                        ],
                        "created_at": service.attrs["CreatedAt"],
                    }
                    service_list.append(service_info)

                except Exception as e:
                    logger.warning(
                        f"Failed to get details for service {service.name}: {e}"
                    )
                    continue

            return {
                "success": True,
                "services": service_list,
                "message": f"Found {len(service_list)} services",
            }

        except Exception as e:
            logger.error(f"Failed to list services: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list services: {str(e)}",
                "services": [],
            }

    def remove_service(self, service_name: str) -> Dict[str, Any]:
        """
        Remove a Docker Swarm service.

        Args:
            service_name: Name of the service to remove

        Returns:
            Dictionary with removal result
        """
        try:
            if not self.swarm_initialized:
                return {
                    "success": False,
                    "error": "Swarm not initialized",
                    "message": "Docker Swarm is not initialized",
                }

            service = self.client.services.get(service_name)
            service.remove()

            # Remove from database if available
            if self.db_manager:
                try:
                    scale_group = self.db_manager.get_scale_group_by_name(service_name)
                    if scale_group:
                        self.db_manager.delete_scale_group(scale_group.id)
                except Exception as e:
                    logger.warning(f"Failed to remove scale group from database: {e}")

            return {
                "success": True,
                "service_name": service_name,
                "message": f"Service {service_name} removed successfully",
            }

        except docker.errors.NotFound:
            return {
                "success": False,
                "error": "Service not found",
                "message": f"Service {service_name} not found",
            }
        except Exception as e:
            logger.error(f"Failed to remove service {service_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to remove service {service_name}: {str(e)}",
            }

    def get_service_logs(self, service_name: str, tail: int = 100) -> Dict[str, Any]:
        """
        Get logs from a Docker Swarm service.

        Args:
            service_name: Name of the service
            tail: Number of log lines to retrieve

        Returns:
            Dictionary with service logs
        """
        try:
            if not self.swarm_initialized:
                return {
                    "success": False,
                    "error": "Swarm not initialized",
                    "message": "Docker Swarm is not initialized",
                }

            service = self.client.services.get(service_name)
            logs = service.logs(tail=tail, timestamps=True, stdout=True, stderr=True)

            return {
                "success": True,
                "service_name": service_name,
                "logs": logs.decode("utf-8") if isinstance(logs, bytes) else logs,
                "message": f"Retrieved logs for service {service_name}",
            }

        except docker.errors.NotFound:
            return {
                "success": False,
                "error": "Service not found",
                "message": f"Service {service_name} not found",
            }
        except Exception as e:
            logger.error(f"Failed to get logs for service {service_name}: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get logs for service {service_name}: {str(e)}",
            }
