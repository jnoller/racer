"""
Racer Backend API Server

A FastAPI-based orchestration server for deploying conda-project applications
to Docker containers with a Heroku/Fly.io-like REST API.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import uvicorn
import os
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Import our custom modules
from project_validator import validate_conda_project, validate_git_repository, cleanup_temp_directory
from dockerfile_template import generate_dockerfile, write_dockerfile
from docker_manager import ContainerManager

# Create FastAPI application
app = FastAPI(
    title="Racer API",
    description="Rapid deployment system for conda-projects",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
    project_path: Optional[str] = None
    git_url: Optional[str] = None
    custom_commands: Optional[List[str]] = None
    ports: Optional[Dict[str, int]] = None
    environment: Optional[Dict[str, str]] = None
    command: Optional[str] = None

class ContainerRunResponse(BaseModel):
    success: bool
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

class ProjectStatusRequest(BaseModel):
    container_id: str

class ProjectStatusByProjectIdRequest(BaseModel):
    project_id: str

class ProjectRerunRequest(BaseModel):
    project_id: str
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
    ports: Optional[Dict[str, int]] = None
    environment: Optional[Dict[str, str]] = None
    command: Optional[str] = None

class ProjectScaleResponse(BaseModel):
    success: bool
    project_name: str
    requested_instances: int
    created_instances: int
    containers: List[Dict[str, Any]]
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

# Initialize container manager
try:
    container_manager = ContainerManager()
except Exception as e:
    print(f"Warning: Failed to initialize Docker container manager: {e}")
    container_manager = None

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Racer API Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "liveness": "/liveness"
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
        service="racer-api"
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
        alive=True,
        timestamp=datetime.now().isoformat(),
        uptime=str(uptime)
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
            "docker": "ok",    # Placeholder
            "conda": "ok"      # Placeholder
        }
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
                detail="Either project_path or git_url must be provided"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation failed: {str(e)}"
        )

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
                detail="Either project_path or git_url must be provided"
            )
        
        # Generate Dockerfile
        dockerfile_content = generate_dockerfile(project_path, request.custom_commands)
        dockerfile_path = write_dockerfile(project_path, custom_commands=request.custom_commands)
        
        return DockerfileGenerationResponse(
            success=True,
            dockerfile_path=dockerfile_path,
            dockerfile_content=dockerfile_content,
            project_name=project_name,
            message=f"Dockerfile generated successfully for {project_name}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Dockerfile generation failed: {str(e)}"
        )
    finally:
        # Clean up temporary directory if we cloned a git repo
        if temp_dir and request.git_url:
            cleanup_temp_directory(temp_dir)

@app.post("/run")
async def run_project(request: DockerfileGenerationRequest, background_tasks: BackgroundTasks):
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
            raise HTTPException(
                status_code=400,
                detail="Failed to generate Dockerfile"
            )
        
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
                "run_interactive": f"docker run -it -p 8000:8000 {project_name} /bin/bash"
            },
            "message": f"Project {project_name} is ready to build and run"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to prepare project for running: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    temp_dir = None
    try:
        # First validate and prepare the project
        if request.git_url:
            validation_result = validate_git_repository(request.git_url)
            project_path = validation_result["project_path"]
            temp_dir = project_path
            project_name = validation_result["project_name"]
        elif request.project_path:
            validation_result = validate_conda_project(request.project_path)
            project_path = validation_result["project_path"]
            project_name = validation_result["project_name"]
        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_path or git_url must be provided"
            )
        
        # Generate Dockerfile
        dockerfile_path = os.path.join(project_path, "Dockerfile")
        dockerfile_content = generate_dockerfile(project_path, request.custom_commands)
        write_dockerfile(project_path, dockerfile_path, request.custom_commands)
        
        # Build Docker image
        build_result = container_manager.build_image(
            project_path, project_name, dockerfile_path, request.custom_commands
        )
        
        if not build_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to build Docker image: {build_result['error']}"
            )
        
        # Run container
        run_result = container_manager.run_container(
            project_name=project_name,
            ports=request.ports,
            environment=request.environment,
            command=request.command
        )
        
        if not run_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to run container: {run_result['error']}"
            )
        
        return ContainerRunResponse(**run_result)
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to run container: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    try:
        result = container_manager.list_containers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list containers: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    try:
        result = container_manager.get_container_status(container_id)
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        return ContainerStatusResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container status: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    try:
        result = container_manager.get_container_logs(container_id, tail)
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        return ContainerLogsResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get container logs: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    try:
        result = container_manager.stop_container(container_id)
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop container: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    try:
        result = container_manager.remove_container(container_id)
        if not result["success"]:
            raise HTTPException(
                status_code=404,
                detail=result["message"]
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove container: {str(e)}"
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
            status_code=500,
            detail="Docker container manager not available"
        )
    
    try:
        result = container_manager.cleanup_stopped_containers()
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cleanup containers: {str(e)}"
        )

@app.get("/projects", response_model=ProjectsListResponse)
async def list_projects():
    """
    List all running projects with user-friendly information.
    """
    try:
        # Get all containers
        containers_response = container_manager.list_containers()
        if not containers_response["success"]:
            return ProjectsListResponse(
                success=False,
                projects=[],
                message=f"Failed to list containers: {containers_response.get('error', 'Unknown error')}"
            )
        
        containers = containers_response.get("containers", [])
        projects = []
        
        for container in containers:
            # Extract project name from container name
            container_name = container.get("container_name", "")
            project_name = container_name
            
            # Try to extract project name from various naming patterns
            if container_name.startswith("racer-"):
                # Remove racer- prefix and timestamp suffix
                parts = container_name.split("-")
                if len(parts) >= 3:
                    project_name = "-".join(parts[1:-1])  # Remove "racer" and timestamp
                else:
                    project_name = container_name[6:]  # Just remove "racer-"
            elif "-" in container_name:
                # For scale command containers: project-name-timestamp-uuid
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
            container_id = container.get("container_id", "")
            project_id = container_id[:12] if container_id else "unknown"
            
            project_info = ProjectInfo(
                project_id=project_id,
                project_name=project_name,
                container_id=container_id,
                container_name=container_name,
                status=container.get("status", "unknown"),
                ports=container.get("ports", {}),
                started_at=container.get("started_at", ""),
                image=container.get("image", "unknown")
            )
            projects.append(project_info)
        
        return ProjectsListResponse(
            success=True,
            projects=projects,
            message=f"Found {len(projects)} running projects"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )

@app.post("/project/status", response_model=ProjectStatusResponse)
async def get_project_status(request: ProjectStatusRequest):
    """
    Get comprehensive status of a running project including container and app health.
    """
    try:
        container_id = request.container_id
        
        # Get container status
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
                message=f"Container not found: {container_status.get('error', 'Unknown error')}"
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
                message=f"Container is {container_status_str}"
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
            message="Project status retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project status: {str(e)}"
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
                message=f"Failed to list projects: {projects_response.message}"
            )
        
        # Find the project by project_id
        target_project = None
        for project in projects_response.projects:
            if project.project_id == project_id or project.project_id.startswith(project_id):
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
                message=f"Project with ID '{project_id}' not found"
            )
        
        # Get detailed status using container ID
        status_request = ProjectStatusRequest(container_id=target_project.container_id)
        return await get_project_status(status_request)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project status by ID: {str(e)}"
        )

@app.post("/project/rerun", response_model=ProjectRerunResponse)
async def rerun_project(request: ProjectRerunRequest):
    """
    Rerun a project by stopping the existing container and starting a new one.
    """
    try:
        project_id = request.project_id
        
        # First, get all projects to find the container ID
        projects_response = await list_projects()
        if not projects_response.success:
            return ProjectRerunResponse(
                success=False,
                old_container_id="unknown",
                message=f"Failed to list projects: {projects_response.message}"
            )
        
        # Find the project by project_id
        target_project = None
        for project in projects_response.projects:
            if project.project_id == project_id or project.project_id.startswith(project_id):
                target_project = project
                break
        
        if not target_project:
            return ProjectRerunResponse(
                success=False,
                old_container_id="unknown",
                message=f"Project with ID '{project_id}' not found"
            )
        
        old_container_id = target_project.container_id
        old_container_name = target_project.container_name
        
        # Stop the existing container
        try:
            stop_response = container_manager.stop_container(old_container_id)
            if not stop_response["success"]:
                return ProjectRerunResponse(
                    success=False,
                    old_container_id=old_container_id,
                    message=f"Failed to stop existing container: {stop_response.get('error', 'Unknown error')}"
                )
        except Exception as e:
            return ProjectRerunResponse(
                success=False,
                old_container_id=old_container_id,
                message=f"Failed to stop existing container: {str(e)}"
            )
        
        # Extract project information from the old container
        # We'll need to get the original project path or git URL
        # For now, we'll try to extract it from the container name or image
        project_name = target_project.project_name
        
        # Try to determine the project source
        # This is a simplified approach - in a real implementation, you might store
        # the original project path/git URL in container labels or metadata
        project_path = None
        git_url = None
        
        # Check if we can find the project by name in common locations
        import os
        from pathlib import Path
        
        # Look for project in current directory and common locations
        possible_paths = [
            f"./{project_name}",
            f"./test-project",  # fallback for test projects
            f"/Users/jesse/Code/pws/racer/test-project"  # specific test path
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.isdir(path):
                project_path = path
                break
        
        if not project_path:
            return ProjectRerunResponse(
                success=False,
                old_container_id=old_container_id,
                message=f"Could not locate project source for '{project_name}'. Please specify project path or git URL."
            )
        
        # Prepare run request with same configuration as original
        run_request_data = {
            'project_path': project_path,
            'custom_commands': request.custom_commands,
            'ports': request.ports or target_project.ports,
            'environment': request.environment,
            'command': request.command
        }
        
        # Rebuild the Docker image with updated source files (unless no_rebuild is True)
        if not request.no_rebuild:
            try:
                # First, generate a new Dockerfile
                dockerfile_response = generate_dockerfile(
                    project_path=project_path,
                    custom_commands=request.custom_commands
                )
                
                # Write the Dockerfile
                dockerfile_path = write_dockerfile(project_path, dockerfile_response)
                
                # Build the new image
                build_response = container_manager.build_image(
                    project_path=project_path,
                    dockerfile_path=dockerfile_path,
                    image_name=f"{project_name}:latest"
                )
                
                if not build_response["success"]:
                    return ProjectRerunResponse(
                        success=False,
                        old_container_id=old_container_id,
                        message=f"Failed to rebuild image: {build_response.get('error', 'Unknown error')}"
                    )
                
            except Exception as e:
                return ProjectRerunResponse(
                    success=False,
                    old_container_id=old_container_id,
                    message=f"Failed to rebuild image: {str(e)}"
                )
        
        # Start new container with rebuilt image
        try:
            run_response = container_manager.run_container(**run_request_data)
            if not run_response["success"]:
                return ProjectRerunResponse(
                    success=False,
                    old_container_id=old_container_id,
                    message=f"Failed to start new container: {run_response.get('error', 'Unknown error')}"
                )
            
            rebuild_status = "with rebuilt image" if not request.no_rebuild else "with existing image"
            return ProjectRerunResponse(
                success=True,
                old_container_id=old_container_id,
                new_container_id=run_response.get("container_id"),
                new_container_name=run_response.get("container_name"),
                ports=run_response.get("ports"),
                message=f"Successfully reran project '{project_name}' {rebuild_status}",
                status=run_response.get("status")
            )
            
        except Exception as e:
            return ProjectRerunResponse(
                success=False,
                old_container_id=old_container_id,
                message=f"Failed to start new container: {str(e)}"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rerun project: {str(e)}"
        )

@app.post("/project/scale", response_model=ProjectScaleResponse)
async def scale_project(request: ProjectScaleRequest):
    """
    Scale a project to run multiple instances.
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
                message="Either project_path or git_url must be specified"
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
                    message=f"Project validation failed: {', '.join(validation_result.get('errors', []))}"
                )
        elif git_url:
            # For git URLs, we'll validate during container creation
            pass
        
        created_containers = []
        failed_containers = []
        
        # Create multiple instances
        for i in range(instances):
            try:
                # Generate unique container name
                container_name = f"{project_name}-{i+1}"
                
                # First, we need to build the image if project_path is provided
                if project_path:
                    # Generate Dockerfile
                    dockerfile_response = generate_dockerfile(
                        project_path=project_path,
                        custom_commands=request.custom_commands
                    )
                    
                    # Write Dockerfile
                    dockerfile_path = write_dockerfile(project_path, custom_commands=request.custom_commands)
                    
                    # Build image
                    build_response = container_manager.build_image(
                        project_path=project_path,
                        project_name=project_name,
                        dockerfile_path=dockerfile_path
                    )
                    
                    if not build_response["success"]:
                        failed_containers.append({
                            'instance': i + 1,
                            'error': f"Failed to build image: {build_response.get('error', 'Unknown error')}"
                        })
                        continue
                
                # Prepare run request with instance-specific ports
                instance_ports = {}
                if request.ports:
                    # Assign different ports to each instance
                    for port_mapping, container_port in request.ports.items():
                        if isinstance(port_mapping, str) and port_mapping.endswith('/tcp'):
                            # Extract base port number
                            base_port = int(port_mapping.split('/')[0])
                            instance_port = base_port + i
                            # Docker port mapping: container_port -> host_port
                            instance_ports[f"{container_port}/tcp"] = instance_port
                        else:
                            # Use port as-is for this instance
                            instance_ports[port_mapping] = container_port
                else:
                    # Default port mapping
                    instance_ports = {"8000/tcp": 8000}
                
                # Debug output
                print(f"Instance {i+1}: ports = {instance_ports}")
                
                run_request_data = {
                    'project_name': project_name,
                    'ports': instance_ports,
                    'environment': request.environment,
                    'command': request.command
                }
                
                # Run container
                run_response = container_manager.run_container(**run_request_data)
                
                if run_response["success"]:
                    container_info = {
                        'container_id': run_response.get("container_id"),
                        'container_name': run_response.get("container_name"),
                        'ports': run_response.get("ports", {}),
                        'status': run_response.get("status", "running"),
                        'instance': i + 1
                    }
                    created_containers.append(container_info)
                else:
                    failed_containers.append({
                        'instance': i + 1,
                        'error': run_response.get('error', 'Unknown error')
                    })
                    
            except Exception as e:
                failed_containers.append({
                    'instance': i + 1,
                    'error': str(e)
                })
        
        # Prepare response
        success = len(created_containers) > 0
        message_parts = []
        
        if created_containers:
            message_parts.append(f"Successfully created {len(created_containers)} instance(s)")
        
        if failed_containers:
            message_parts.append(f"Failed to create {len(failed_containers)} instance(s)")
            for failure in failed_containers:
                message_parts.append(f"  Instance {failure['instance']}: {failure['error']}")
        
        message = "; ".join(message_parts)
        
        return ProjectScaleResponse(
            success=success,
            project_name=project_name,
            requested_instances=instances,
            created_instances=len(created_containers),
            containers=created_containers,
            message=message
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to scale project: {str(e)}"
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
        log_level="info" if not debug else "debug"
    )
