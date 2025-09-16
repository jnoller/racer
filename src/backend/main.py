"""
Racer Backend API Server

A FastAPI-based orchestration server for deploying conda-project applications
to Docker containers with a Heroku/Fly.io-like REST API.

API Structure:
- /api/v1/ - User-facing endpoints (matches CLI commands)
- /admin/ - Administrative endpoints (matches racerctl commands)
- / - System endpoints (health, liveness, etc.)
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
    from database import DatabaseManager
except ImportError:
    from .database import DatabaseManager

# Create FastAPI application
app = FastAPI(
    title="Racer API",
    description="Rapid deployment system for conda-projects",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ============================================================================
# RESPONSE MODELS
# ============================================================================


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    service: str


class LivenessResponse(BaseModel):
    alive: bool
    timestamp: str


class ProjectValidationRequest(BaseModel):
    project_path: Optional[str] = None
    git_url: Optional[str] = None


class ProjectValidationResponse(BaseModel):
    success: bool
    message: str
    project_name: Optional[str] = None
    issues: Optional[List[str]] = None


class DockerfileGenerationRequest(BaseModel):
    project_name: str
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[str] = None
    environment: Optional[str] = None
    command: Optional[str] = None


class DockerfileGenerationResponse(BaseModel):
    success: bool
    message: str
    project_name: Optional[str] = None
    dockerfile_path: Optional[str] = None
    dockerfile_content: Optional[str] = None
    instructions: Optional[Dict[str, str]] = None


class ContainerRunRequest(BaseModel):
    project_name: str
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[str] = None
    environment: Optional[str] = None
    command: Optional[str] = None
    app_port: Optional[int] = None


class ContainerRunResponse(BaseModel):
    success: bool
    message: str
    project_name: Optional[str] = None
    container_id: Optional[str] = None
    project_id: Optional[str] = None
    host_ports: Optional[Dict[str, int]] = None


class ProjectsListResponse(BaseModel):
    success: bool
    message: str
    projects: List[Dict[str, Any]]


class ProjectStatusRequest(BaseModel):
    project_name: str


class ProjectStatusResponse(BaseModel):
    success: bool
    message: str
    project_name: Optional[str] = None
    status: Optional[str] = None
    container_id: Optional[str] = None
    project_id: Optional[str] = None
    host_ports: Optional[Dict[str, int]] = None
    app_health: Optional[Dict[str, Any]] = None


class ProjectRerunRequest(BaseModel):
    project_name: str
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[str] = None
    environment: Optional[str] = None
    command: Optional[str] = None
    app_port: Optional[int] = None


class ProjectRerunResponse(BaseModel):
    success: bool
    message: str
    project_name: Optional[str] = None
    container_id: Optional[str] = None
    project_id: Optional[str] = None
    host_ports: Optional[Dict[str, int]] = None


class ProjectScaleRequest(BaseModel):
    project_name: str
    instances: int
    app_port: Optional[int] = None


class ProjectScaleResponse(BaseModel):
    success: bool
    message: str
    project_name: Optional[str] = None
    service_name: Optional[str] = None
    instances: Optional[int] = None
    host_ports: Optional[Dict[str, int]] = None


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "Racer API",
        "version": "0.1.0",
        "description": "Rapid deployment system for conda-projects",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0",
        service="racer-api",
    )


@app.get("/liveness", response_model=LivenessResponse)
async def liveness_check():
    """Liveness check endpoint."""
    return LivenessResponse(alive=True, timestamp=datetime.now().isoformat())


@app.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # Check if required services are available
    try:
        # Initialize managers if not already done
        global container_manager, swarm_manager, db_manager

        if container_manager is None:
            container_manager = ContainerManager()
        if swarm_manager is None:
            swarm_manager = SwarmManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        return {"ready": True, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")


# ============================================================================
# USER-FACING API ENDPOINTS (/api/v1/)
# ============================================================================


@app.post("/api/v1/validate", response_model=ProjectValidationResponse)
async def validate_project(request: ProjectValidationRequest):
    """
    Validate a conda-project directory or git repository.

    This endpoint matches: racer validate
    """
    try:
        if request.project_path:
            # Validate local project
            result = validate_conda_project(request.project_path)
            if result["valid"]:
                return ProjectValidationResponse(
                    success=True,
                    message="Project is valid",
                    project_name=result.get("project_name"),
                    issues=result.get("issues", []),
                )
            else:
                return ProjectValidationResponse(
                    success=False,
                    message="Project validation failed",
                    issues=result.get("issues", []),
                )
        elif request.git_url:
            # Validate git repository
            result = validate_git_repository(request.git_url)
            if result["valid"]:
                return ProjectValidationResponse(
                    success=True,
                    message="Git repository is valid",
                    project_name=result.get("project_name"),
                    issues=result.get("issues", []),
                )
            else:
                return ProjectValidationResponse(
                    success=False,
                    message="Git repository validation failed",
                    issues=result.get("issues", []),
                )
        else:
            return ProjectValidationResponse(
                success=False, message="Either project_path or git_url must be provided"
            )
    except Exception as e:
        return ProjectValidationResponse(
            success=False, message=f"Validation error: {str(e)}"
        )


@app.post("/api/v1/dockerfile", response_model=DockerfileGenerationResponse)
async def generate_dockerfile_endpoint(request: DockerfileGenerationRequest):
    """
    Generate a Dockerfile for a conda-project.

    This endpoint matches: racer dockerfile
    """
    try:
        # Initialize managers if needed
        global container_manager, db_manager
        if container_manager is None:
            container_manager = ContainerManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        # Generate project ID
        project_id = str(uuid.uuid4())

        # Determine project path
        if request.project_path:
            project_path = request.project_path
        elif request.git_url:
            # For git URLs, we need to clone first - this is a limitation
            return DockerfileGenerationResponse(
                success=False,
                message="Dockerfile generation from git URL not supported in this endpoint. Use deploy instead.",
            )
        else:
            return DockerfileGenerationResponse(
                success=False,
                message="Either project_path or git_url must be provided",
            )

        # Generate Dockerfile content
        dockerfile_content = generate_dockerfile(project_path, request.custom_commands)
        
        # Write Dockerfile to file
        dockerfile_path = write_dockerfile(project_path, custom_commands=request.custom_commands)

        # For backward compatibility, also return build instructions
        instructions = {
            "build": f"docker build -t {request.project_name} -f {dockerfile_path} .",
            "run": f"docker run -p 8000:8000 {request.project_name}",
            "run_interactive": f"docker run -it -p 8000:8000 {request.project_name} /bin/bash",
        }

        return DockerfileGenerationResponse(
            success=True,
            message="Dockerfile generated successfully",
            project_name=request.project_name,
            dockerfile_path=dockerfile_path,
            dockerfile_content=dockerfile_content,
            instructions=instructions,
        )
    except Exception as e:
        return DockerfileGenerationResponse(
            success=False, message=f"Dockerfile generation error: {str(e)}"
        )


@app.post("/api/v1/deploy", response_model=ContainerRunResponse)
async def deploy_project(request: ContainerRunRequest):
    """
    Deploy a conda-project by building and running a Docker container.

    This endpoint matches: racer deploy
    """
    try:
        # Initialize managers if needed
        global container_manager, db_manager
        if container_manager is None:
            container_manager = ContainerManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        # Generate project ID
        project_id = str(uuid.uuid4())

        # Parse environment variables
        env_vars = {}
        if request.environment:
            for env_pair in request.environment.split(","):
                if "=" in env_pair:
                    key, value = env_pair.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        # Run container
        run_result = container_manager.run_container(
            project_name=request.project_name,
            project_path=request.project_path,
            git_url=request.git_url,
            custom_commands=request.custom_commands,
            environment=env_vars,
            command=request.command,
            app_port=request.app_port,
            project_id=project_id,
        )

        if run_result["success"]:
            # Store in database
            db_manager.add_project(
                project_id=project_id,
                project_name=request.project_name,
                container_id=run_result["container_id"],
                project_path=request.project_path,
                git_url=request.git_url,
            )

            return ContainerRunResponse(
                success=True,
                message=f"Project {request.project_name} deployed successfully",
                project_name=request.project_name,
                container_id=run_result["container_id"],
                project_id=project_id,
                host_ports=run_result.get("host_ports", {}),
            )
        else:
            return ContainerRunResponse(
                success=False,
                message=f"Failed to deploy project: {run_result.get('error', 'Unknown error')}",
            )
    except Exception as e:
        return ContainerRunResponse(
            success=False, message=f"Deployment error: {str(e)}"
        )


@app.get("/api/v1/projects", response_model=ProjectsListResponse)
async def list_projects():
    """
    List all running projects.

    This endpoint matches: racer list
    """
    try:
        # Initialize managers if needed
        global container_manager, swarm_manager, db_manager
        if container_manager is None:
            container_manager = ContainerManager()
        if swarm_manager is None:
            swarm_manager = SwarmManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        # Get projects from database
        projects = db_manager.list_projects()

        # Get container and swarm information
        containers = container_manager.list_containers()
        swarm_response = swarm_manager.list_services()
        swarm_services = (
            swarm_response.get("services", [])
            if isinstance(swarm_response, dict)
            else []
        )

        # Combine information
        project_list = []
        for project in projects:
            project_info = {
                "project_id": project.id,
                "project_name": project.name,
                "container_id": None,
                "status": "unknown",
                "type": "container",
                "image": project.image_name,
                "started_at": project.created_at.isoformat()
                if project.created_at
                else "unknown",
            }

            # Get containers for this project
            project_containers = db_manager.get_project_containers(project.name)
            if project_containers:
                # Use the most recent container
                latest_container = project_containers[-1]
                project_info["container_id"] = latest_container.container_id

                # Check container status
                if latest_container.container_id in containers:
                    container_info = containers[latest_container.container_id]
                    project_info["status"] = container_info["status"]
                    project_info["host_ports"] = container_info.get("ports", {})

            # Check swarm service status
            service_name = f"racer-{project.name}"
            for service in swarm_services:
                if service.get("name") == service_name:
                    project_info["status"] = service.get("status", "unknown")
                    project_info["type"] = "swarm"
                    project_info["instances"] = service.get("instances", 1)
                    project_info["host_ports"] = service.get("ports", {})
                    break

            project_list.append(project_info)

        return ProjectsListResponse(
            success=True,
            message=f"Found {len(project_list)} projects",
            projects=project_list,
        )
    except Exception as e:
        return ProjectsListResponse(
            success=False, message=f"Failed to list projects: {str(e)}", projects=[]
        )


@app.post("/api/v1/status", response_model=ProjectStatusResponse)
async def get_project_status(request: ProjectStatusRequest):
    """
    Get comprehensive status of a running project.

    This endpoint matches: racer status
    """
    try:
        # Initialize managers if needed
        global container_manager, swarm_manager, db_manager
        if container_manager is None:
            container_manager = ContainerManager()
        if swarm_manager is None:
            swarm_manager = SwarmManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        # Get project from database
        project = db_manager.get_project_by_name(request.project_name)
        if not project:
            return ProjectStatusResponse(
                success=False, message=f"Project '{request.project_name}' not found"
            )

        project_info = {
            "project_id": project["project_id"],
            "project_name": project["project_name"],
            "container_id": project["container_id"],
            "status": "unknown",
            "type": "container",
        }

        # Check container status
        if project["container_id"]:
            container_info = container_manager.get_container_status(
                project["container_id"]
            )
            if container_info:
                project_info["status"] = container_info["status"]
                project_info["host_ports"] = container_info.get("ports", {})

        # Check swarm service status
        service_name = f"racer-{project['project_name']}"
        service_info = swarm_manager.get_service_status(service_name)
        if service_info:
            project_info["status"] = service_info["status"]
            project_info["type"] = "swarm"
            project_info["instances"] = service_info.get("instances", 1)
            project_info["host_ports"] = service_info.get("ports", {})

        return ProjectStatusResponse(
            success=True,
            message=f"Project '{request.project_name}' status retrieved",
            project_name=project["project_name"],
            status=project_info["status"],
            container_id=project["container_id"],
            project_id=project["project_id"],
            host_ports=project_info.get("host_ports", {}),
            app_health=project_info.get("app_health"),
        )
    except Exception as e:
        return ProjectStatusResponse(
            success=False, message=f"Failed to get project status: {str(e)}"
        )


@app.post("/api/v1/rerun", response_model=ProjectRerunResponse)
async def rerun_project(request: ProjectRerunRequest):
    """
    Rerun a project by stopping the existing container and starting a new one.

    This endpoint matches: racer rerun
    """
    try:
        # Initialize managers if needed
        global container_manager, swarm_manager, db_manager
        if container_manager is None:
            container_manager = ContainerManager()
        if swarm_manager is None:
            swarm_manager = SwarmManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        # Get existing project
        project = db_manager.get_project_by_name(request.project_name)
        if not project:
            return ProjectRerunResponse(
                success=False, message=f"Project '{request.project_name}' not found"
            )

        # Stop existing container/service
        if project["container_id"]:
            container_manager.stop_container(project["container_id"])

        # Stop swarm service if it exists
        service_name = f"racer-{project['project_name']}"
        swarm_manager.remove_service(service_name)

        # Generate new project ID
        new_project_id = str(uuid.uuid4())

        # Parse environment variables
        env_vars = {}
        if request.environment:
            for env_pair in request.environment.split(","):
                if "=" in env_pair:
                    key, value = env_pair.split("=", 1)
                    env_vars[key.strip()] = value.strip()

        # Run new container
        run_result = container_manager.run_container(
            project_name=request.project_name,
            project_path=request.project_path or project.get("project_path"),
            git_url=request.git_url or project.get("git_url"),
            custom_commands=request.custom_commands,
            environment=env_vars,
            command=request.command,
            app_port=request.app_port,
            project_id=new_project_id,
        )

        if run_result["success"]:
            # Update database
            db_manager.update_project(
                project_id=new_project_id,
                project_name=request.project_name,
                container_id=run_result["container_id"],
                project_path=request.project_path or project.get("project_path"),
                git_url=request.git_url or project.get("git_url"),
            )

            return ProjectRerunResponse(
                success=True,
                message=f"Project {request.project_name} rerun successfully",
                project_name=request.project_name,
                container_id=run_result["container_id"],
                project_id=new_project_id,
                host_ports=run_result.get("host_ports", {}),
            )
        else:
            return ProjectRerunResponse(
                success=False,
                message=f"Failed to rerun project: {run_result.get('error', 'Unknown error')}",
            )
    except Exception as e:
        return ProjectRerunResponse(success=False, message=f"Rerun error: {str(e)}")


@app.post("/api/v1/scale", response_model=ProjectScaleResponse)
async def scale_project(request: ProjectScaleRequest):
    """
    Scale a project to run multiple instances using Docker Swarm.

    This endpoint matches: racer scale
    """
    try:
        # Initialize managers if needed
        global container_manager, swarm_manager, db_manager
        if container_manager is None:
            container_manager = ContainerManager()
        if swarm_manager is None:
            swarm_manager = SwarmManager()
        if db_manager is None:
            db_manager = DatabaseManager()

        # Get existing project
        project = db_manager.get_project_by_name(request.project_name)
        if not project:
            return ProjectScaleResponse(
                success=False, message=f"Project '{request.project_name}' not found"
            )

        # Stop existing container
        if project["container_id"]:
            container_manager.stop_container(project["container_id"])

        # Create swarm service
        service_name = f"racer-{request.project_name}"
        scale_result = swarm_manager.scale_service(
            service_name=service_name,
            project_name=request.project_name,
            project_path=project.get("project_path"),
            git_url=project.get("git_url"),
            instances=request.instances,
            app_port=request.app_port,
        )

        if scale_result["success"]:
            return ProjectScaleResponse(
                success=True,
                message=f"Project {request.project_name} scaled to {request.instances} instances",
                project_name=request.project_name,
                service_name=service_name,
                instances=request.instances,
                host_ports=scale_result.get("host_ports", {}),
            )
        else:
            return ProjectScaleResponse(
                success=False,
                message=f"Failed to scale project: {scale_result.get('error', 'Unknown error')}",
            )
    except Exception as e:
        return ProjectScaleResponse(success=False, message=f"Scale error: {str(e)}")


# ============================================================================
# ADMIN API ENDPOINTS (/admin/)
# ============================================================================


@app.get("/admin/containers", response_model=Dict[str, Any])
async def list_containers():
    """
    List all containers (admin endpoint).

    This endpoint matches: racerctl containers list
    """
    try:
        global container_manager
        if container_manager is None:
            container_manager = ContainerManager()

        containers_response = container_manager.list_containers()
        if (
            isinstance(containers_response, dict)
            and "containers" in containers_response
        ):
            containers = containers_response["containers"]
        else:
            containers = (
                containers_response if isinstance(containers_response, list) else []
            )

        return {
            "success": True,
            "message": f"Found {len(containers)} containers",
            "containers": containers,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to list containers: {str(e)}",
            "containers": {},
        }


@app.get("/admin/containers/{container_id}/status", response_model=Dict[str, Any])
async def get_container_status(container_id: str):
    """
    Get status of a specific container (admin endpoint).

    This endpoint matches: racerctl containers status
    """
    try:
        global container_manager
        if container_manager is None:
            container_manager = ContainerManager()

        status = container_manager.get_container_status(container_id)
        if status:
            return {
                "success": True,
                "message": f"Container {container_id} status retrieved",
                "container_id": container_id,
                "status": status,
            }
        else:
            return {"success": False, "message": f"Container {container_id} not found"}
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get container status: {str(e)}",
        }


@app.get("/admin/containers/{container_id}/logs", response_model=Dict[str, Any])
async def get_container_logs(container_id: str, tail: int = 100):
    """
    Get logs from a specific container (admin endpoint).

    This endpoint matches: racerctl containers logs
    """
    try:
        global container_manager
        if container_manager is None:
            container_manager = ContainerManager()

        logs = container_manager.get_container_logs(container_id, tail=tail)
        return {
            "success": True,
            "message": f"Container {container_id} logs retrieved",
            "container_id": container_id,
            "logs": logs,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get container logs: {str(e)}",
            "logs": "",
        }


@app.post("/admin/containers/{container_id}/stop")
async def stop_container(container_id: str):
    """
    Stop a specific container (admin endpoint).

    This endpoint matches: racerctl containers stop
    """
    try:
        global container_manager
        if container_manager is None:
            container_manager = ContainerManager()

        result = container_manager.stop_container(container_id)
        if result["success"]:
            return {
                "success": True,
                "message": f"Container {container_id} stopped successfully",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to stop container: {result.get('error', 'Unknown error')}",
            }
    except Exception as e:
        return {"success": False, "message": f"Failed to stop container: {str(e)}"}


@app.delete("/admin/containers/{container_id}")
async def remove_container(container_id: str):
    """
    Remove a specific container (admin endpoint).

    This endpoint matches: racerctl containers remove
    """
    try:
        global container_manager
        if container_manager is None:
            container_manager = ContainerManager()

        result = container_manager.remove_container(container_id)
        if result["success"]:
            return {
                "success": True,
                "message": f"Container {container_id} removed successfully",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to remove container: {result.get('error', 'Unknown error')}",
            }
    except Exception as e:
        return {"success": False, "message": f"Failed to remove container: {str(e)}"}


@app.post("/admin/containers/cleanup")
async def cleanup_containers():
    """
    Clean up all stopped containers (admin endpoint).

    This endpoint matches: racerctl containers cleanup
    """
    try:
        global container_manager
        if container_manager is None:
            container_manager = ContainerManager()

        result = container_manager.cleanup_containers()
        return {
            "success": True,
            "message": f"Cleanup completed: {result.get('message', 'Success')}",
            "removed_containers": result.get("removed_containers", []),
        }
    except Exception as e:
        return {"success": False, "message": f"Failed to cleanup containers: {str(e)}"}


@app.get("/admin/swarm/services", response_model=Dict[str, Any])
async def list_swarm_services():
    """
    List all Docker Swarm services (admin endpoint).

    This endpoint matches: racerctl swarm status
    """
    try:
        global swarm_manager
        if swarm_manager is None:
            swarm_manager = SwarmManager()

        services_response = swarm_manager.list_services()
        if isinstance(services_response, dict) and "services" in services_response:
            services = services_response["services"]
        else:
            services = services_response if isinstance(services_response, list) else []

        return {
            "success": True,
            "message": f"Found {len(services)} swarm services",
            "services": services,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to list swarm services: {str(e)}",
            "services": {},
        }


@app.get("/admin/swarm/service/{service_name}/status", response_model=Dict[str, Any])
async def get_swarm_service_status(service_name: str):
    """
    Get status of a specific Docker Swarm service (admin endpoint).

    This endpoint matches: racerctl swarm status
    """
    try:
        global swarm_manager
        if swarm_manager is None:
            swarm_manager = SwarmManager()

        status = swarm_manager.get_service_status(service_name)
        if status:
            return {
                "success": True,
                "message": f"Service {service_name} status retrieved",
                "service_name": service_name,
                "status": status,
            }
        else:
            return {"success": False, "message": f"Service {service_name} not found"}
    except Exception as e:
        return {"success": False, "message": f"Failed to get service status: {str(e)}"}


@app.get("/admin/swarm/service/{service_name}/logs", response_model=Dict[str, Any])
async def get_swarm_service_logs(service_name: str, tail: int = 100):
    """
    Get logs from a specific Docker Swarm service (admin endpoint).

    This endpoint matches: racerctl swarm logs
    """
    try:
        global swarm_manager
        if swarm_manager is None:
            swarm_manager = SwarmManager()

        logs = swarm_manager.get_service_logs(service_name, tail=tail)
        return {
            "success": True,
            "message": f"Service {service_name} logs retrieved",
            "service_name": service_name,
            "logs": logs,
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to get service logs: {str(e)}",
            "logs": "",
        }


@app.delete("/admin/swarm/service/{service_name}", response_model=Dict[str, Any])
async def remove_swarm_service(service_name: str):
    """
    Remove a specific Docker Swarm service (admin endpoint).

    This endpoint matches: racerctl swarm remove
    """
    try:
        global swarm_manager
        if swarm_manager is None:
            swarm_manager = SwarmManager()

        result = swarm_manager.remove_service(service_name)
        if result["success"]:
            return {
                "success": True,
                "message": f"Service {service_name} removed successfully",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to remove service: {result.get('error', 'Unknown error')}",
            }
    except Exception as e:
        return {"success": False, "message": f"Failed to remove service: {str(e)}"}


# ============================================================================
# LEGACY ENDPOINTS (for backward compatibility)
# ============================================================================


@app.post("/run")
async def run_project_legacy(
    request: DockerfileGenerationRequest, background_tasks: BackgroundTasks
):
    """
    Legacy endpoint for run preparation (backward compatibility).

    This endpoint is deprecated. Use /api/v1/dockerfile instead.
    """
    # Redirect to new endpoint
    return await generate_dockerfile_endpoint(request)


@app.post("/containers/run", response_model=ContainerRunResponse)
async def run_container_legacy(request: ContainerRunRequest):
    """
    Legacy endpoint for container execution (backward compatibility).

    This endpoint is deprecated. Use /api/v1/deploy instead.
    """
    # Redirect to new endpoint
    return await deploy_project(request)


# ============================================================================
# INITIALIZATION
# ============================================================================

# Global managers
container_manager = None
swarm_manager = None
db_manager = None

if __name__ == "__main__":
    uvicorn.run(
        "main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True
    )
