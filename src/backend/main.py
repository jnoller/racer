"""
Racer Backend API Server

A FastAPI-based orchestration server for deploying conda-project applications
to Docker containers with a Heroku/Fly.io-like REST API.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import os
import uuid
from datetime import datetime

# Import our custom modules
from project_validator import (
    validate_conda_project,
    validate_git_repository,
    cleanup_temp_directory,
)
from dockerfile_template import generate_dockerfile, write_dockerfile
from docker_manager import ContainerManager
from swarm_manager import SwarmManager

try:
    from .database import DatabaseManager
except ImportError:
    from database import DatabaseManager

# Create FastAPI application
app = FastAPI(
    title="Racer API",
    description="Rapid deployment system for conda-projects",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    service: str


class LivenessResponse(BaseModel):
    alive: bool
    timestamp: str
    uptime: str


class ProjectValidationRequest(BaseModel):
    project_path: Optional[str] = None
    git_url: Optional[str] = None


class ProjectValidationResponse(BaseModel):
    valid: bool
    project_name: str
    project_version: str
    environments: List[str]
    channels: List[str]
    dependencies: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    project_path: str
    git_url: Optional[str] = None


class DockerfileGenerationRequest(BaseModel):
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[List[str]] = None


class DockerfileGenerationResponse(BaseModel):
    success: bool
    dockerfile_path: str
    dockerfile_content: str
    project_name: str
    message: str


class ContainerRunRequest(BaseModel):
    project_name: str
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[List[str]] = None
    app_port: Optional[int] = None
    ports: Optional[Dict[str, int]] = None
    environment: Optional[Dict[str, str]] = None
    command: Optional[str] = None


class ContainerRunResponse(BaseModel):
    success: bool
    project_id: Optional[str] = None
    container_id: Optional[str] = None
    container_name: Optional[str] = None
    ports: Optional[Dict[str, int]] = None
    message: str
    status: Optional[str] = None


class ContainerStatusResponse(BaseModel):
    success: bool
    container_id: str
    container_name: str
    status: str
    ports: Dict[str, int]
    started_at: str
    stopped_at: Optional[str] = None
    image: str


class ContainerLogsResponse(BaseModel):
    success: bool
    container_id: str
    logs: str


class ProjectStatusByContainerIdRequest(BaseModel):
    container_id: str


class ProjectStatusByProjectIdRequest(BaseModel):
    project_id: str


class ProjectStatusByProjectNameRequest(BaseModel):
    project_name: str


class ProjectStatusRequest(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    container_id: Optional[str] = None


class ProjectRerunRequest(BaseModel):
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    custom_commands: Optional[List[str]] = None
    ports: Optional[Dict[str, int]] = None
    environment: Optional[Dict[str, str]] = None
    command: Optional[str] = None
    no_rebuild: Optional[bool] = False


class ProjectRerunResponse(BaseModel):
    success: bool
    old_container_id: str
    new_container_id: Optional[str] = None
    new_container_name: Optional[str] = None
    ports: Optional[Dict[str, int]] = None
    message: str
    status: Optional[str] = None


class ProjectScaleRequest(BaseModel):
    project_name: str
    instances: int = 1
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[List[str]] = None
    app_port: Optional[int] = None
    ports: Optional[Dict[str, int]] = None
    environment: Optional[Dict[str, str]] = None
    command: Optional[str] = None


class ProjectScaleResponse(BaseModel):
    success: bool
    project_name: str
    requested_instances: int
    created_instances: int
    containers: List[Dict[str, Any]]
    compose_file: Optional[str] = None
    message: str


class ProjectStatusResponse(BaseModel):
    success: bool
    container_id: str
    container_name: str
    container_status: str
    app_health: Optional[Dict[str, Any]] = None
    app_accessible: bool = False
    ports: Dict[str, int]
    started_at: str
    image: str
    message: str


class ProjectInfo(BaseModel):
    project_id: str
    project_name: str
    container_id: str
    container_name: str
    status: str
    ports: Dict[str, int]
    started_at: str
    image: str


class ProjectsListResponse(BaseModel):
    success: bool
    projects: List[ProjectInfo]
    message: str


# Global variables for tracking
start_time = datetime.now()

# Initialize database manager
try:
    db_manager = DatabaseManager()
    db_manager.init_database()
    print("Database initialized successfully")
except Exception as e:
    print(f"Warning: Failed to initialize database: {e}")
    db_manager = None

# Initialize container manager
try:
    container_manager = ContainerManager(db_manager=db_manager)
except Exception as e:
    print(f"Warning: Failed to initialize Docker container manager: {e}")
    container_manager = None

# Initialize swarm manager
try:
    swarm_manager = SwarmManager(db_manager=db_manager)
except Exception as e:
    print(f"Warning: Failed to initialize Docker Swarm manager: {e}")
    swarm_manager = None


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Racer API Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "liveness": "/liveness",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring service health.

    Returns:
        HealthResponse: Service health status and metadata
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0",
        service="racer-api",
    )


@app.get("/liveness", response_model=LivenessResponse)
async def liveness_check():
    """
    Liveness probe endpoint for container orchestration.

    This endpoint is used by container orchestrators (like Kubernetes)
    to determine if the service is alive and should continue running.

    Returns:
        LivenessResponse: Service liveness status and uptime
    """
    uptime = datetime.now() - start_time
    return LivenessResponse(
        alive=True, timestamp=datetime.now().isoformat(), uptime=str(uptime)
    )


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint for container orchestration.

    This endpoint indicates if the service is ready to accept traffic.
    In a full implementation, this would check database connections,
    external dependencies, etc.

    Returns:
        dict: Readiness status
    """
    # For now, always ready. In production, check dependencies here.
    return {
        "ready": True,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": "ok",  # Placeholder
            "docker": "ok",  # Placeholder
            "conda": "ok",  # Placeholder
        },
    }


@app.post("/validate", response_model=ProjectValidationResponse)
async def validate_project(request: ProjectValidationRequest):
    """
    Validate a conda-project directory or git repository.

    Args:
        request: ProjectValidationRequest with either project_path or git_url

    Returns:
        ProjectValidationResponse with validation results
    """
    try:
        if request.project_path:
            # Validate local directory
            validation_result = validate_conda_project(request.project_path)
            return ProjectValidationResponse(**validation_result)

        elif request.git_url:
            # Validate git repository
            validation_result = validate_git_repository(request.git_url)
            return ProjectValidationResponse(**validation_result)

        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_path or git_url must be provided",
            )

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Validation failed: {str(e)}")


@app.post("/dockerfile", response_model=DockerfileGenerationResponse)
async def generate_dockerfile_endpoint(request: DockerfileGenerationRequest):
    """
    Generate a Dockerfile for a conda-project.

    Args:
        request: DockerfileGenerationRequest with project details

    Returns:
        DockerfileGenerationResponse with generated Dockerfile
    """
    temp_dir = None
    try:
        if request.git_url:
            # Clone and validate git repository
            validation_result = validate_git_repository(request.git_url)
            project_path = validation_result["project_path"]
            temp_dir = project_path  # Mark for cleanup
            project_name = validation_result["project_name"]

        elif request.project_path:
            # Validate local directory
            validation_result = validate_conda_project(request.project_path)
            project_path = validation_result["project_path"]
            project_name = validation_result["project_name"]

        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_path or git_url must be provided",
            )

        # Generate Dockerfile
        dockerfile_content = generate_dockerfile(project_path, request.custom_commands)
        dockerfile_path = write_dockerfile(
            project_path, custom_commands=request.custom_commands
        )

        return DockerfileGenerationResponse(
            success=True,
            dockerfile_path=dockerfile_path,
            dockerfile_content=dockerfile_content,
            project_name=project_name,
            message=f"Dockerfile generated successfully for {project_name}",
        )

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Dockerfile generation failed: {str(e)}"
        )
    finally:
        # Clean up temporary directory if we cloned a git repo
        if temp_dir and request.git_url:
            cleanup_temp_directory(temp_dir)


@app.post("/run")
async def run_project(
    request: DockerfileGenerationRequest, background_tasks: BackgroundTasks
):
    """
    Run a conda-project by generating Dockerfile and building/running container.

    This is a simplified version that generates the Dockerfile and returns
    instructions for building and running the container.

    Args:
        request: DockerfileGenerationRequest with project details
        background_tasks: FastAPI background tasks

    Returns:
        dict: Instructions for building and running the container
    """
    try:
        # First generate the Dockerfile
        dockerfile_response = await generate_dockerfile_endpoint(request)

        if not dockerfile_response.success:
            raise HTTPException(status_code=400, detail="Failed to generate Dockerfile")

        # Return build and run instructions
        project_name = dockerfile_response.project_name
        dockerfile_path = dockerfile_response.dockerfile_path

        return {
            "success": True,
            "project_name": project_name,
            "dockerfile_path": dockerfile_path,
            "instructions": {
                "build": f"docker build -t {project_name} -f {dockerfile_path} .",
                "run": f"docker run -p 8000:8000 {project_name}",
                "run_interactive": f"docker run -it -p 8000:8000 {project_name} /bin/bash",
            },
            "message": f"Project {project_name} is ready to build and run",
        }

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to prepare project for running: {str(e)}"
        )


@app.post("/containers/run", response_model=ContainerRunResponse)
async def run_container(request: ContainerRunRequest):
    """
    Build and run a Docker container for a conda-project.

    Args:
        request: ContainerRunRequest with project details and run options

    Returns:
        ContainerRunResponse with container information
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    temp_dir = None
    try:
        # Use the provided project name
        project_name = request.project_name

        # Auto-generate a unique project ID
        project_id = str(uuid.uuid4())

        # First validate and prepare the project
        if request.git_url:
            validation_result = validate_git_repository(request.git_url)
            project_path = validation_result["project_path"]
            temp_dir = project_path
        elif request.project_path:
            validation_result = validate_conda_project(request.project_path)
            project_path = validation_result["project_path"]
        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_path or git_url must be provided",
            )

        # Generate Dockerfile
        dockerfile_path = os.path.join(project_path, "Dockerfile")
        write_dockerfile(project_path, dockerfile_path, request.custom_commands)

        # Build Docker image
        build_result = container_manager.build_image(
            project_path, project_name, dockerfile_path, request.custom_commands
        )

        if not build_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to build Docker image: {build_result['error']}",
            )

        # Prepare ports for container
        ports = None
        if request.app_port is not None:
            # Use app_port for simplified load balancing - auto-assign host port
            from port_manager import get_random_port, get_service_port_range
            try:
                host_port = get_random_port(*get_service_port_range())
                ports = {f"{request.app_port}/tcp": host_port}
            except RuntimeError:
                # Fallback to high port range
                host_port = get_random_port(9000, 10000)
                ports = {f"{request.app_port}/tcp": host_port}
        elif request.ports:
            # Use legacy port mappings
            ports = request.ports

        # Run container
        run_result = container_manager.run_container(
            project_name=project_name,
            ports=ports,
            environment=request.environment,
            command=request.command,
        )

        if not run_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to run container: {run_result['error']}",
            )

        # Add the generated project_id to the response
        run_result["project_id"] = project_id
        return ContainerRunResponse(**run_result)

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to run container: {str(e)}"
        )
    finally:
        # Clean up temporary directory if we cloned a git repo
        if temp_dir and request.git_url:
            cleanup_temp_directory(temp_dir)


@app.get("/containers", response_model=Dict[str, Any])
async def list_containers():
    """
    List all tracked containers.

    Returns:
        Dictionary with container list
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    try:
        result = container_manager.list_containers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list containers: {str(e)}"
        )


@app.get("/containers/{container_id}/status", response_model=ContainerStatusResponse)
async def get_container_status(container_id: str):
    """
    Get the status of a specific container.

    Args:
        container_id: ID of the container

    Returns:
        ContainerStatusResponse with container status
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    try:
        result = container_manager.get_container_status(container_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return ContainerStatusResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get container status: {str(e)}"
        )


@app.get("/containers/{container_id}/logs", response_model=ContainerLogsResponse)
async def get_container_logs(container_id: str, tail: int = 100):
    """
    Get logs from a specific container.

    Args:
        container_id: ID of the container
        tail: Number of lines to return

    Returns:
        ContainerLogsResponse with container logs
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    try:
        result = container_manager.get_container_logs(container_id, tail)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return ContainerLogsResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get container logs: {str(e)}"
        )


@app.post("/containers/{container_id}/stop")
async def stop_container(container_id: str):
    """
    Stop a running container.

    Args:
        container_id: ID of the container to stop

    Returns:
        Dictionary with stop results
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    try:
        result = container_manager.stop_container(container_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to stop container: {str(e)}"
        )


@app.delete("/containers/{container_id}")
async def remove_container(container_id: str):
    """
    Remove a container.

    Args:
        container_id: ID of the container to remove

    Returns:
        Dictionary with removal results
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    try:
        result = container_manager.remove_container(container_id)
        if not result["success"]:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove container: {str(e)}"
        )


@app.post("/containers/cleanup")
async def cleanup_containers():
    """
    Clean up stopped containers.

    Returns:
        Dictionary with cleanup results
    """
    if container_manager is None:
        raise HTTPException(
            status_code=500, detail="Docker container manager not available"
        )

    try:
        result = container_manager.cleanup_stopped_containers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to cleanup containers: {str(e)}"
        )


@app.get("/projects", response_model=ProjectsListResponse)
async def list_projects():
    """
    List all running projects with user-friendly information.
    Includes tracked containers and Docker Swarm services.
    """
    try:
        projects = []

        # 1. Get tracked containers from ContainerManager
        containers_response = container_manager.list_containers()
        if containers_response["success"]:
            containers = containers_response.get("containers", [])
            for container in containers:
                container_name = container.get("container_name", "")
                container_id = container.get("container_id", "")

                # Try to get project name from database first
                project_name = container_name  # fallback
                if db_manager:
                    try:
                        db_container = db_manager.get_container(container_id)
                        if db_container and db_container.project:
                            project_name = db_container.project.name
                    except Exception:
                        # If database lookup fails, fall back to container name extraction
                        pass

                # If database lookup failed or not available, extract from container name
                if project_name == container_name:
                    # Try to extract project name from various naming patterns
                    if container_name.startswith("racer-"):
                        # Remove racer- prefix and timestamp suffix
                        parts = container_name.split("-")
                        if len(parts) >= 3:
                            project_name = "-".join(
                                parts[1:-1]
                            )  # Remove "racer" and timestamp
                        else:
                            project_name = container_name[6:]  # Just remove "racer-"
                    elif "-" in container_name:
                        # Handle patterns like "readme-test-1757950934-29c6dc53"
                        # Extract the base project name (everything before the first timestamp)
                        parts = container_name.split("-")
                        if len(parts) >= 3:
                            # Find the first part that looks like a timestamp (all digits)
                            project_parts = []
                            for part in parts:
                                if part.isdigit() and len(part) > 8:  # Timestamp-like
                                    break
                                project_parts.append(part)
                            if project_parts:
                                project_name = "-".join(project_parts)

                # Create project ID (short container ID for user reference)
                project_id = container_id[:12] if container_id else "unknown"

                project_info = ProjectInfo(
                    project_id=project_id,
                    project_name=project_name,
                    container_id=container_id,
                    container_name=container_name,
                    status=container.get("status", "unknown"),
                    ports=container.get("ports", {}),
                    started_at=container.get("started_at", ""),
                    image=container.get("image", "unknown"),
                )
                projects.append(project_info)

        # 2. Get Docker Swarm services
        if swarm_manager:
            try:
                swarm_services_response = swarm_manager.list_services()
                if swarm_services_response["success"]:
                    swarm_services = swarm_services_response.get("services", [])
                    for service in swarm_services:
                        service_name = service.get("service_name", "")
                        service_id = service.get("service_id", "")

                        # Check if this service is already in our projects list
                        already_tracked = any(
                            p.container_id == service_id
                            or p.project_name == service_name
                            for p in projects
                        )

                        if not already_tracked:
                            # Create project info for swarm service
                            project_info = ProjectInfo(
                                project_id=service_id[:12] if service_id else "unknown",
                                project_name=service_name,
                                container_id=service_id,
                                container_name=service_name,  # Swarm services don't have individual container names
                                status=service.get("status", "unknown"),
                                ports=service.get("ports", {}),
                                started_at=service.get("created_at", ""),
                                image=service.get("image", "unknown"),
                            )
                            projects.append(project_info)

            except Exception as e:
                print(f"Warning: Could not detect Docker Swarm services: {e}")

        return ProjectsListResponse(
            success=True,
            projects=projects,
            message=f"Found {len(projects)} running projects",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list projects: {str(e)}"
        )


@app.post("/project/status", response_model=ProjectStatusResponse)
async def get_project_status(request: ProjectStatusRequest):
    """
    Get comprehensive status of a running project including container and app health.
    """
    try:
        project_id = request.project_id
        project_name = request.project_name
        container_id = request.container_id

        # Validate that at least one identifier is provided
        if not project_id and not project_name and not container_id:
            return ProjectStatusResponse(
                success=False,
                container_id="unknown",
                container_name="unknown",
                container_status="invalid_request",
                app_health=None,
                app_accessible=False,
                ports={},
                started_at="",
                image="unknown",
                message="Either project_id, project_name, or container_id must be provided",
            )

        # First, get all projects to find the container ID
        projects_response = await list_projects()
        if not projects_response.success:
            return ProjectStatusResponse(
                success=False,
                container_id="unknown",
                container_name="unknown",
                container_status="error",
                app_health=None,
                app_accessible=False,
                ports={},
                started_at="",
                image="unknown",
                message=f"Failed to list projects: {projects_response.message}",
            )

        # Find the project by project_id, project_name, or container_id
        target_project = None
        for project in projects_response.projects:
            if container_id and (
                project.container_id == container_id
                or project.container_id.startswith(container_id)
            ):
                target_project = project
                break
            elif project_id and (
                project.project_id == project_id
                or project.project_id.startswith(project_id)
            ):
                target_project = project
                break
            elif project_name and project.project_name == project_name:
                target_project = project
                break

        if not target_project:
            return ProjectStatusResponse(
                success=False,
                container_id=container_id or "unknown",
                container_name="unknown",
                container_status="not_found",
                app_health=None,
                app_accessible=False,
                ports={},
                started_at="",
                image="unknown",
                message=f"Project not found",
            )

        container_id = target_project.container_id
        project_name = target_project.project_name

        # Check if this is a swarm service first
        if swarm_manager:
            try:
                swarm_status = swarm_manager.get_service_status(project_name)
                if swarm_status["success"]:
                    # This is a swarm service
                    return ProjectStatusResponse(
                        success=True,
                        container_id=swarm_status["service_id"],
                        container_name=swarm_status["service_name"],
                        container_status=swarm_status["status"],
                        app_health=None,  # TODO: Add health check for swarm services
                        app_accessible=swarm_status["status"] == "running",
                        ports=swarm_status["ports"],
                        started_at=swarm_status["created_at"],
                        image=swarm_status["image"],
                        message=f"Swarm service status: {swarm_status['running_replicas']}/{swarm_status['replicas']} replicas running",
                    )
            except Exception:
                # If swarm service lookup fails, continue with container lookup
                pass

        # Get container status (for individual containers)
        container_status = container_manager.get_container_status(container_id)
        if not container_status["success"]:
            return ProjectStatusResponse(
                success=False,
                container_id=container_id,
                container_name="unknown",
                container_status="not_found",
                app_health=None,
                app_accessible=False,
                ports={},
                started_at="",
                image="unknown",
                message=f"Container not found: {container_status.get('error', 'Unknown error')}",
            )

        # Extract container info
        container_name = container_status["container_name"]
        container_status_str = container_status["status"]
        ports = container_status["ports"]
        started_at = container_status["started_at"]
        image = container_status["image"]

        # Check if container is running
        if container_status_str != "running":
            return ProjectStatusResponse(
                success=True,
                container_id=container_id,
                container_name=container_name,
                container_status=container_status_str,
                app_health=None,
                app_accessible=False,
                ports=ports,
                started_at=started_at,
                image=image,
                message=f"Container is {container_status_str}",
            )

        # Try to check app health if container is running
        app_health = None
        app_accessible = False

        try:
            import requests
            import time

            # Find the internal port (usually 8000)
            internal_port = None
            for port_mapping in ports.values():
                if isinstance(port_mapping, dict) and "8000/tcp" in port_mapping:
                    internal_port = 8000
                    break

            if internal_port:
                # Try to reach the app's health endpoint
                health_url = f"http://localhost:{list(ports.keys())[0]}/health"

                # Give the app a moment to start up
                time.sleep(0.5)

                response = requests.get(health_url, timeout=5)
                if response.status_code == 200:
                    app_health = response.json()
                    app_accessible = True

        except Exception as e:
            # App health check failed, but container is running
            app_health = {"error": f"Health check failed: {str(e)}"}
            app_accessible = False

        return ProjectStatusResponse(
            success=True,
            container_id=container_id,
            container_name=container_name,
            container_status=container_status_str,
            app_health=app_health,
            app_accessible=app_accessible,
            ports=ports,
            started_at=started_at,
            image=image,
            message="Project status retrieved successfully",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get project status: {str(e)}"
        )


@app.post("/project/status-by-id", response_model=ProjectStatusResponse)
async def get_project_status_by_id(request: ProjectStatusByProjectIdRequest):
    """
    Get comprehensive status of a running project by project ID.
    """
    try:
        project_id = request.project_id

        # First, get all projects to find the container ID
        projects_response = await list_projects()
        if not projects_response.success:
            return ProjectStatusResponse(
                success=False,
                container_id="unknown",
                container_name="unknown",
                container_status="not_found",
                app_health=None,
                app_accessible=False,
                ports={},
                started_at="",
                image="unknown",
                message=f"Failed to list projects: {projects_response.message}",
            )

        # Find the project by project_id
        target_project = None
        for project in projects_response.projects:
            if project.project_id == project_id or project.project_id.startswith(
                project_id
            ):
                target_project = project
                break

        if not target_project:
            return ProjectStatusResponse(
                success=False,
                container_id="unknown",
                container_name="unknown",
                container_status="not_found",
                app_health=None,
                app_accessible=False,
                ports={},
                started_at="",
                image="unknown",
                message=f"Project with ID '{project_id}' not found",
            )

        # Get detailed status using project_id
        status_request = ProjectStatusRequest(project_id=target_project.project_id)
        return await get_project_status(status_request)

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get project status by ID: {str(e)}"
        )


@app.post("/project/rerun", response_model=ProjectRerunResponse)
async def rerun_project(request: ProjectRerunRequest):
    """
    Rerun a project by stopping the existing container and starting a new one.
    """
    try:
        project_id = request.project_id
        project_name = request.project_name

        # Validate that either project_id or project_name is provided
        if not project_id and not project_name:
            return ProjectRerunResponse(
                success=False,
                old_container_id="unknown",
                message="Either project_id or project_name must be provided",
            )

        # First, get all projects to find the container ID
        projects_response = await list_projects()
        if not projects_response.success:
            return ProjectRerunResponse(
                success=False,
                old_container_id="unknown",
                message=f"Failed to list projects: {projects_response.message}",
            )

        # Find the project by project_id or project_name
        target_project = None
        for project in projects_response.projects:
            if project_id and (
                project.project_id == project_id
                or project.project_id.startswith(project_id)
            ):
                target_project = project
                break
            elif project_name and project.project_name == project_name:
                target_project = project
                break

        if not target_project:
            return ProjectRerunResponse(
                success=False,
                old_container_id="unknown",
                message=f"Project with ID '{project_id}' not found",
            )

        old_container_id = target_project.container_id

        # Stop the existing container
        try:
            stop_response = container_manager.stop_container(old_container_id)
            if not stop_response["success"]:
                return ProjectRerunResponse(
                    success=False,
                    old_container_id=old_container_id,
                    message=f"Failed to stop existing container: {stop_response.get('error', 'Unknown error')}",
                )
        except Exception as e:
            return ProjectRerunResponse(
                success=False,
                old_container_id=old_container_id,
                message=f"Failed to stop existing container: {str(e)}",
            )

        # Extract project information from the old container
        # We'll need to get the original project path or git URL
        # For now, we'll try to extract it from the container name or image
        project_name = target_project.project_name

        # Try to determine the project source
        # This is a simplified approach - in a real implementation, you might store
        # the original project path/git URL in container labels or metadata
        project_path = None

        # Check if we can find the project by name in common locations
        import os

        # Look for project in current directory and common locations
        possible_paths = [
            f"./{project_name}",
            "./test-project",  # fallback for test projects
            "/Users/jesse/Code/pws/racer/test-project",  # specific test path
        ]

        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                project_path = path
                break

        if not project_path:
            return ProjectRerunResponse(
                success=False,
                old_container_id=old_container_id,
                message=(
                    f"Could not locate project source for '{project_name}'. "
                    f"Please specify project path or git URL."
                ),
            )

        # Prepare run request with same configuration as original
        run_request_data = {
            "project_name": project_name,
            "ports": request.ports or target_project.ports,
            "environment": request.environment,
            "command": request.command,
        }

        # Rebuild the Docker image with updated source files (unless no_rebuild is True)
        if not request.no_rebuild:
            try:
                # Write the Dockerfile
                dockerfile_path = write_dockerfile(
                    project_path, custom_commands=request.custom_commands
                )

                # Build the new image
                build_response = container_manager.build_image(
                    project_path=project_path,
                    project_name=project_name,
                    dockerfile_path=dockerfile_path,
                    custom_commands=request.custom_commands,
                )

                if not build_response["success"]:
                    return ProjectRerunResponse(
                        success=False,
                        old_container_id=old_container_id,
                        message=f"Failed to rebuild image: {build_response.get('error', 'Unknown error')}",
                    )

            except Exception as e:
                return ProjectRerunResponse(
                    success=False,
                    old_container_id=old_container_id,
                    message=f"Failed to rebuild image: {str(e)}",
                )

        # Start new container with rebuilt image
        try:
            run_response = container_manager.run_container(**run_request_data)
            if not run_response["success"]:
                return ProjectRerunResponse(
                    success=False,
                    old_container_id=old_container_id,
                    message=f"Failed to start new container: {run_response.get('error', 'Unknown error')}",
                )

            rebuild_status = (
                "with rebuilt image"
                if not request.no_rebuild
                else "with existing image"
            )
            return ProjectRerunResponse(
                success=True,
                old_container_id=old_container_id,
                new_container_id=run_response.get("container_id"),
                new_container_name=run_response.get("container_name"),
                ports=run_response.get("ports"),
                message=f"Successfully reran project '{project_name}' {rebuild_status}",
                status=run_response.get("status"),
            )

        except Exception as e:
            return ProjectRerunResponse(
                success=False,
                old_container_id=old_container_id,
                message=f"Failed to start new container: {str(e)}",
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to rerun project: {str(e)}"
        )


@app.post("/project/scale", response_model=ProjectScaleResponse)
async def scale_project(request: ProjectScaleRequest):
    """
    Scale a project to run multiple instances using Docker Swarm.
    """
    try:
        project_name = request.project_name
        instances = request.instances
        project_path = request.project_path
        git_url = request.git_url

        if not project_path and not git_url:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message="Either project_path or git_url must be specified",
            )

        # Check if swarm manager is available
        if not swarm_manager:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message="Docker Swarm manager not available",
            )

        # Validate project if path is provided
        if project_path:
            validation_result = validate_conda_project(project_path)
            if not validation_result["valid"]:
                return ProjectScaleResponse(
                    success=False,
                    project_name=project_name,
                    requested_instances=instances,
                    created_instances=0,
                    containers=[],
                    message=f"Project validation failed: {', '.join(validation_result.get('errors', []))}",
                )
        elif git_url:
            # For git URLs, we'll validate during container creation
            pass

        # Generate Dockerfile first
        dockerfile_path = None
        if project_path:
            # Write Dockerfile
            dockerfile_path = os.path.join(project_path, "Dockerfile")
            write_dockerfile(project_path, dockerfile_path, request.custom_commands)

        # Build Docker image
        image_name = f"{project_name}:latest"
        build_result = container_manager.build_image(
            project_path or ".",
            project_name,
            dockerfile_path or os.path.join(project_path or ".", "Dockerfile"),
            request.custom_commands,
        )

        if not build_result["success"]:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message=f"Failed to build image: {build_result.get('error', 'Unknown error')}",
            )

        # Prepare ports for swarm service
        ports = {}
        if request.app_port is not None:
            # Use app_port for simplified load balancing - auto-assign host port
            from port_manager import get_random_port, get_service_port_range
            try:
                host_port = get_random_port(*get_service_port_range())
                ports[f"{request.app_port}"] = host_port
            except RuntimeError:
                # Fallback to high port range
                host_port = get_random_port(9000, 10000)
                ports[f"{request.app_port}"] = host_port
        elif request.ports:
            # For swarm, we use the first port mapping as the published port
            # All replicas will be accessible through the same port with load balancing
            for container_port, host_port in request.ports.items():
                ports[container_port] = host_port
        else:
            ports = {"8000": 8000}  # Default port

        # Prepare environment variables
        environment = request.environment or {}

        # Prepare command
        command = request.command or ["conda", "project", "run"]

        # Create or update swarm service
        service_result = swarm_manager.create_service(
            service_name=project_name,
            image=image_name,
            replicas=instances,
            ports=ports,
            environment=environment,
            command=command,
        )

        if not service_result["success"]:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message=f"Failed to create swarm service: {service_result.get('error', 'Unknown error')}",
            )

        # Get service status to verify it's running
        service_status = swarm_manager.get_service_status(project_name)

        created_containers = []
        if service_status["success"]:
            # Create container info for each replica
            for i in range(instances):
                container_info = {
                    "container_id": f"{service_status['service_id'][:12]}_{i+1}",
                    "container_name": f"{project_name}_{i+1}",
                    "ports": ports,
                    "status": service_status["status"],
                    "instance": i + 1,
                }
                created_containers.append(container_info)

        # Prepare response
        success = service_result["success"] and len(created_containers) > 0
        message = f"Successfully scaled {project_name} to {instances} instance(s) using Docker Swarm"

        return ProjectScaleResponse(
            success=success,
            project_name=project_name,
            requested_instances=instances,
            created_instances=len(created_containers),
            containers=created_containers,
            compose_file=None,  # Not used for swarm
            message=message,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scale project: {str(e)}"
        )


@app.post("/project/scale-up", response_model=ProjectScaleResponse)
async def scale_up_project(request: ProjectScaleRequest):
    """
    Scale up an existing project to more instances using Docker Swarm.
    """
    try:
        project_name = request.project_name
        instances = request.instances

        if not swarm_manager:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message="Docker Swarm manager not available",
            )

        # Scale the existing service
        scale_result = swarm_manager.scale_service(project_name, instances)

        if not scale_result["success"]:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message=f"Failed to scale service: {scale_result.get('error', 'Unknown error')}",
            )

        # Get updated service status
        service_status = swarm_manager.get_service_status(project_name)

        created_containers = []
        if service_status["success"]:
            # Create container info for each replica
            for i in range(instances):
                container_info = {
                    "container_id": f"{service_status['service_id'][:12]}_{i+1}",
                    "container_name": f"{project_name}_{i+1}",
                    "ports": service_status.get("ports", {}),
                    "status": service_status["status"],
                    "instance": i + 1,
                }
                created_containers.append(container_info)

        return ProjectScaleResponse(
            success=True,
            project_name=project_name,
            requested_instances=instances,
            created_instances=len(created_containers),
            containers=created_containers,
            compose_file=None,
            message=f"Successfully scaled {project_name} to {instances} instances",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scale up project: {str(e)}"
        )


@app.post("/project/scale-down", response_model=ProjectScaleResponse)
async def scale_down_project(request: ProjectScaleRequest):
    """
    Scale down an existing project to fewer instances using Docker Swarm.
    """
    try:
        project_name = request.project_name
        instances = request.instances

        if not swarm_manager:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message="Docker Swarm manager not available",
            )

        # Scale the existing service
        scale_result = swarm_manager.scale_service(project_name, instances)

        if not scale_result["success"]:
            return ProjectScaleResponse(
                success=False,
                project_name=project_name,
                requested_instances=instances,
                created_instances=0,
                containers=[],
                message=f"Failed to scale service: {scale_result.get('error', 'Unknown error')}",
            )

        # Get updated service status
        service_status = swarm_manager.get_service_status(project_name)

        created_containers = []
        if service_status["success"]:
            # Create container info for each replica
            for i in range(instances):
                container_info = {
                    "container_id": f"{service_status['service_id'][:12]}_{i+1}",
                    "container_name": f"{project_name}_{i+1}",
                    "ports": service_status.get("ports", {}),
                    "status": service_status["status"],
                    "instance": i + 1,
                }
                created_containers.append(container_info)

        return ProjectScaleResponse(
            success=True,
            project_name=project_name,
            requested_instances=instances,
            created_instances=len(created_containers),
            containers=created_containers,
            compose_file=None,
            message=f"Successfully scaled {project_name} down to {instances} instances",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to scale down project: {str(e)}"
        )


@app.get("/swarm/services", response_model=Dict[str, Any])
async def list_swarm_services():
    """
    List all Docker Swarm services.
    """
    try:
        if not swarm_manager:
            return {
                "success": False,
                "services": [],
                "message": "Docker Swarm manager not available",
            }

        result = swarm_manager.list_services()
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to list swarm services: {str(e)}"
        )


@app.get("/swarm/service/{service_name}/status", response_model=Dict[str, Any])
async def get_swarm_service_status(service_name: str):
    """
    Get the status of a specific Docker Swarm service.
    """
    try:
        if not swarm_manager:
            return {"success": False, "message": "Docker Swarm manager not available"}

        result = swarm_manager.get_service_status(service_name)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get service status: {str(e)}"
        )


@app.get("/swarm/service/{service_name}/logs", response_model=Dict[str, Any])
async def get_swarm_service_logs(service_name: str, tail: int = 100):
    """
    Get logs from a Docker Swarm service.
    """
    try:
        if not swarm_manager:
            return {"success": False, "message": "Docker Swarm manager not available"}

        result = swarm_manager.get_service_logs(service_name, tail)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get service logs: {str(e)}"
        )


@app.delete("/swarm/service/{service_name}", response_model=Dict[str, Any])
async def remove_swarm_service(service_name: str):
    """
    Remove a Docker Swarm service.
    """
    try:
        if not swarm_manager:
            return {"success": False, "message": "Docker Swarm manager not available"}

        result = swarm_manager.remove_service(service_name)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to remove service: {str(e)}"
        )


if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"

    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug",
    )
