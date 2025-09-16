"""
Racer CLI - User-facing commands for running conda-projects.
"""

import click
import json
from api import RacerAPIClient, RacerAPIError


@click.group()
@click.option("--api-url", default="http://localhost:8001", help="Racer API server URL")
@click.option("--timeout", default=30, type=int, help="Request timeout in seconds")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, api_url: str, timeout: int, verbose: bool):
    """
    Racer - Rapid deployment system for conda-projects.

    This tool provides user-facing commands to run and manage your conda-projects
    in Docker containers with a single command.
    """
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url
    ctx.obj["timeout"] = timeout
    ctx.obj["verbose"] = verbose


@cli.command()
@click.option(
    "--project-name",
    "-n",
    "project_name",
    required=True,
    help="Name for the project (used for container naming)",
)
@click.option(
    "--path", "-p", "project_path", help="Path to local conda-project directory"
)
@click.option(
    "--git", "-g", "git_url", help="Git repository URL containing conda-project"
)
@click.option(
    "--custom-commands",
    "-c",
    help="Custom RUN commands to add to Dockerfile (comma-separated)",
)
@click.option("--app-port", type=int, help="Port that your application exposes (for load balancing)")
@click.option(
    "--env",
    "-e",
    "environment",
    help="Environment variables (format: KEY=VALUE,KEY=VALUE)",
)
@click.option("--command", help="Override command to run in container")
@click.option(
    "--build-only", is_flag=True, help="Only build the Docker image, do not run"
)
@click.pass_context
def deploy(
    ctx,
    project_name: str,
    project_path: str,
    git_url: str,
    custom_commands: str,
    app_port: int,
    environment: str,
    command: str,
    build_only: bool,
):
    """
    Run a conda-project by building and running a Docker container.

    This command builds a Docker image from a conda-project and runs it in a container.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    if not project_path and not git_url:
        click.echo(
            click.style("Error: Either --path or --git must be specified", fg="red"),
            err=True,
        )
        ctx.exit(1)

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # Prepare request data
        request_data = {"project_name": project_name}
        if project_path:
            request_data["project_path"] = project_path
        if git_url:
            request_data["git_url"] = git_url
        if custom_commands:
            request_data["custom_commands"] = [
                cmd.strip() for cmd in custom_commands.split(",")
            ]
        # Handle port configuration
        if app_port is not None:
            # Use --app-port for simplified load balancing
            request_data["app_port"] = app_port
        if environment:
            # Parse environment variables
            env_vars = {}
            for env_var in environment.split(","):
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env_vars[key] = value
            request_data["environment"] = env_vars
        if command:
            request_data["command"] = command

        if build_only:
            # Use the new /api/v1/dockerfile endpoint for build-only
            response = client._make_request("POST", "/api/v1/dockerfile", json=request_data)

            if verbose:
                click.echo("Build preparation response:")
                click.echo(json.dumps(response, indent=2))
            else:
                if response.get("success", False):
                    click.echo(
                        click.style("✓ Project prepared for building", fg="green")
                    )
                    click.echo(f"Project: {response.get('project_name', 'unknown')}")
                    click.echo(
                        f"Dockerfile: {response.get('dockerfile_path', 'unknown')}"
                    )

                    # Show build instructions
                    instructions = response.get("instructions", {})
                    if instructions:
                        click.echo("\nBuild command:")
                        click.echo(f"  {instructions.get('build', 'N/A')}")
                else:
                    click.echo(
                        click.style(
                            "✗ Failed to prepare project for building", fg="red"
                        )
                    )
        else:
            # Use the new /api/v1/deploy endpoint for actual container execution
            response = client._make_request(
                "POST", "/api/v1/deploy", json=request_data
            )

            if verbose:
                click.echo("Container run response:")
                click.echo(json.dumps(response, indent=2))
            else:
                if response.get("success", False):
                    click.echo(
                        click.style("✓ Container started successfully", fg="green")
                    )
                    click.echo(
                        f"Container ID: {response.get('container_id', 'unknown')}"
                    )
                    click.echo(
                        f"Container Name: {response.get('container_name', 'unknown')}"
                    )
                    click.echo(f"Status: {response.get('status', 'unknown')}")

                    # Show port mappings
                    port_mappings = response.get("ports", {})
                    if port_mappings:
                        click.echo("Port mappings:")
                        for container_port, host_port in port_mappings.items():
                            click.echo(f"  {host_port} -> {container_port}")

                    click.echo(f"\nMessage: {response.get('message', '')}")
                    click.echo(
                        "\nUse 'racerctl containers list' to see all running containers"
                    )
                    click.echo(
                        "Use 'racerctl containers logs <container_id>' to view logs"
                    )
                else:
                    click.echo(click.style("✗ Failed to start container", fg="red"))
                    click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.option(
    "--path", "-p", "project_path", help="Path to local conda-project directory"
)
@click.option(
    "--git", "-g", "git_url", help="Git repository URL containing conda-project"
)
@click.pass_context
def validate(ctx, project_path: str, git_url: str):
    """
    Validate a conda-project directory or git repository.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    if not project_path and not git_url:
        click.echo(
            click.style("Error: Either --path or --git must be specified", fg="red"),
            err=True,
        )
        ctx.exit(1)

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # Prepare request data
        request_data = {}
        if project_path:
            request_data["project_path"] = project_path
        if git_url:
            request_data["git_url"] = git_url

        # Make API request
        response = client._make_request("POST", "/api/v1/validate", json=request_data)

        if verbose:
            click.echo("Validation response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("valid", False):
                click.echo(click.style("✓ Project is valid", fg="green"))
                click.echo(f"Project: {response.get('project_name', 'unknown')}")
                click.echo(f"Version: {response.get('project_version', 'unknown')}")
                click.echo(
                    f"Environments: {', '.join(response.get('environments', []))}"
                )
                click.echo(f"Channels: {', '.join(response.get('channels', []))}")

                # Show warnings if any
                warnings = response.get("warnings", [])
                if warnings:
                    click.echo("\nWarnings:")
                    for warning in warnings:
                        click.echo(click.style(f"  ⚠ {warning}", fg="yellow"))
            else:
                click.echo(click.style("✗ Project is invalid", fg="red"))
                errors = response.get("errors", [])
                for error in errors:
                    click.echo(click.style(f"  ✗ {error}", fg="red"))

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.option(
    "--path", "-p", "project_path", help="Path to local conda-project directory"
)
@click.option(
    "--git", "-g", "git_url", help="Git repository URL containing conda-project"
)
@click.option(
    "--custom-commands",
    "-c",
    help="Custom RUN commands to add to Dockerfile (comma-separated)",
)
@click.pass_context
def dockerfile(ctx, project_path: str, git_url: str, custom_commands: str):
    """
    Generate a Dockerfile for a conda-project.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    if not project_path and not git_url:
        click.echo(
            click.style("Error: Either --path or --git must be specified", fg="red"),
            err=True,
        )
        ctx.exit(1)

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # Prepare request data
        request_data = {}
        if project_path:
            request_data["project_path"] = project_path
        if git_url:
            request_data["git_url"] = git_url
        if custom_commands:
            request_data["custom_commands"] = [
                cmd.strip() for cmd in custom_commands.split(",")
            ]

        # Make API request
        response = client._make_request("POST", "/api/v1/dockerfile", json=request_data)

        if verbose:
            click.echo("Dockerfile generation response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                click.echo(
                    click.style("✓ Dockerfile generated successfully", fg="green")
                )
                click.echo(f"Project: {response.get('project_name', 'unknown')}")
                click.echo(f"Dockerfile: {response.get('dockerfile_path', 'unknown')}")

                # Show Dockerfile content
                dockerfile_content = response.get("dockerfile_content", "")
                if dockerfile_content:
                    click.echo("\nDockerfile content:")
                    click.echo("-" * 50)
                    click.echo(dockerfile_content)
            else:
                click.echo(click.style("✗ Failed to generate Dockerfile", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.option(
    "--project-name",
    "-n",
    "project_name",
    help="Project name to check status for (shows all instances)",
)
@click.option("--project-id", "-p", "project_id", help="Project ID to check status for")
@click.option(
    "--container-id",
    "-c",
    "container_id",
    help="Container ID to check status for (legacy)",
)
@click.option(
    "--list", "list_projects", is_flag=True, help="List all running projects first"
)
@click.pass_context
def status(
    ctx, project_name: str, project_id: str, container_id: str, list_projects: bool
):
    """
    Check the status of a running project or list all projects.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    # Validate that at least one identifier is provided (unless listing all projects)
    if not list_projects and not project_name and not project_id and not container_id:
        click.echo(
            click.style(
                "Error: At least one of --project-name, --project-id, --container-id, or --list must be specified",
                fg="red",
            ),
            err=True,
        )
        ctx.exit(1)

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # If list flag is set, show all projects
        if list_projects:
            projects_response = client._make_request("GET", "/api/v1/projects")
            if projects_response.get("success"):
                projects = projects_response.get("projects", [])
                if projects:
                    click.echo("Running projects:")
                    for project in projects:
                        click.echo(
                            f"  • {project['project_name']} (ID: {project['project_id']})"
                        )
                        click.echo(f"    Status: {project['status']}")
                        click.echo(f"    Ports: {project.get('ports', {})}")
                        click.echo()
                else:
                    click.echo("No running projects found.")
            else:
                click.echo(click.style("Failed to list projects", fg="red"), err=True)
            return

        # Handle project name - show all instances of that project
        if project_name:
            projects_response = client._make_request("GET", "/api/v1/projects")
            if projects_response.get("success"):
                projects = projects_response.get("projects", [])
                matching_projects = [
                    p for p in projects if p["project_name"] == project_name
                ]

                if not matching_projects:
                    click.echo(
                        f"No running instances found for project '{project_name}'"
                    )
                    return

                click.echo(
                    f"Project '{project_name}' instances ({len(matching_projects)}):"
                )
                click.echo()

                for project in matching_projects:
                    container_name = project.get("container_name", "unknown")
                    container_status = project.get("status", "unknown")
                    ports = project.get("ports", {})
                    started_at = project.get("started_at", "unknown")

                    click.echo(f"  • {container_name}")
                    click.echo(f"    ID: {project['project_id']}")
                    click.echo(f"    Status: {container_status}")
                    click.echo(f"    Started: {started_at}")
                    if ports:
                        click.echo(f"    Ports: {ports}")
                    click.echo()

                return
            else:
                click.echo(click.style("Failed to list projects", fg="red"), err=True)
                return

        # If no project name, project ID or container ID provided, list projects and ask user to choose
        if not project_id and not container_id:
            projects_response = client._make_request("GET", "/api/v1/projects")
            if projects_response.get("success"):
                projects = projects_response.get("projects", [])
                if not projects:
                    click.echo("No running projects found.")
                    click.echo("Use 'racer deploy' to start a project first.")
                    return

                if len(projects) == 1:
                    project_id = projects[0]["project_id"]
                    click.echo(
                        f"Checking status for project: {projects[0]['project_name']}"
                    )
                else:
                    click.echo(
                        "Multiple projects running. Please specify --project-name or --project-id:"
                    )
                    for i, project in enumerate(projects, 1):
                        click.echo(
                            f"  {i}. {project['project_name']} (ID: {project['project_id']})"
                        )
                    return
            else:
                click.echo(click.style("Failed to list projects", fg="red"), err=True)
                return

        # Get project status using project name
        status_response = client._make_request(
            "POST", "/api/v1/status", json={"project_name": project_name}
        )

        if verbose:
            click.echo("Status response:")
            click.echo(json.dumps(status_response, indent=2))
        else:
            if status_response.get("success"):
                container_name = status_response.get("container_name", "unknown")
                container_status = status_response.get("container_status", "unknown")
                app_accessible = status_response.get("app_accessible", False)
                ports = status_response.get("ports", {})
                started_at = status_response.get("started_at", "unknown")
                image = status_response.get("image", "unknown")

                click.echo(f"Container: {container_name}")
                if container_id:
                    click.echo(f"ID: {container_id[:12]}")
                else:
                    click.echo(
                        f"ID: {status_response.get('container_id', 'unknown')[:12]}"
                    )
                click.echo(f"Status: {container_status}")
                click.echo(f"Image: {image}")
                click.echo(f"Started: {started_at}")

                if ports:
                    click.echo("Ports:")
                    for host_port, container_port in ports.items():
                        click.echo(f"  {host_port} -> {container_port}")

                # App health status
                if container_status == "running":
                    if app_accessible:
                        app_health = status_response.get("app_health", {})
                        click.echo(
                            click.style("✓ Application is accessible", fg="green")
                        )
                        if app_health:
                            click.echo(
                                f"App Status: {app_health.get('status', 'unknown')}"
                            )
                            if "service" in app_health:
                                click.echo(f"Service: {app_health['service']}")
                    else:
                        click.echo(
                            click.style("⚠ Application not accessible", fg="yellow")
                        )
                        app_health = status_response.get("app_health", {})
                        if app_health and "error" in app_health:
                            click.echo(f"Error: {app_health['error']}")
                else:
                    click.echo(
                        click.style(f"⚠ Container is {container_status}", fg="yellow")
                    )

                message = status_response.get("message", "")
                if message:
                    click.echo(f"Message: {message}")
            else:
                click.echo(click.style("✗ Failed to get project status", fg="red"))
                error_msg = status_response.get("message", "Unknown error")
                click.echo(f"Error: {error_msg}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def list(ctx, verbose: bool):
    """
    List all running projects.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # Get projects list
        projects_response = client._make_request("GET", "/api/v1/projects")

        if projects_response.get("success"):
            projects = projects_response.get("projects", [])

            if verbose:
                click.echo("Projects response:")
                click.echo(json.dumps(projects_response, indent=2))
            else:
                if projects:
                    click.echo(f"Running projects ({len(projects)}):")
                    click.echo()
                    for project in projects:
                        click.echo(f"  • {project['project_name']}")
                        click.echo(f"    ID: {project['project_id']}")
                        click.echo(f"    Status: {project['status']}")
                        click.echo(f"    Image: {project['image']}")
                        click.echo(f"    Started: {project['started_at']}")
                        if project.get("ports"):
                            click.echo(f"    Ports: {project['ports']}")
                        click.echo()
                else:
                    click.echo("No running projects found.")
                    click.echo("Use 'racer deploy' to start a project first.")
        else:
            click.echo(click.style("Failed to list projects", fg="red"), err=True)
            error_msg = projects_response.get("message", "Unknown error")
            click.echo(f"Error: {error_msg}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.option(
    "--project-name",
    "-n",
    "project_name",
    required=True,
    help="Name for the project (used for container naming)",
)
@click.option(
    "--instances",
    "-i",
    "instances",
    default=1,
    type=int,
    help="Number of instances to create",
)
@click.option(
    "--path", "-p", "project_path", help="Path to local conda-project directory"
)
@click.option(
    "--git", "-g", "git_url", help="Git repository URL containing conda-project"
)
@click.option(
    "--custom-commands",
    "-c",
    help="Custom RUN commands to add to Dockerfile (comma-separated)",
)
@click.option("--app-port", type=int, help="Port that your application exposes (for load balancing)")
@click.option(
    "--environment",
    "-e",
    help="Environment variables (format: KEY=VALUE, comma-separated)",
)
@click.option("--command", help="Override the default command to run")
@click.pass_context
def scale(
    ctx,
    project_name: str,
    instances: int,
    project_path: str,
    git_url: str,
    custom_commands: str,
    app_port: int,
    environment: str,
    command: str,
):
    """
    Scale a project to run multiple instances.
    """
    api_url = ctx.obj["api_url"]
    timeout = max(ctx.obj["timeout"], 120)  # Scale operations need more time
    verbose = ctx.obj["verbose"]

    if not project_path and not git_url:
        click.echo(
            click.style("Error: Either --path or --git must be specified", fg="red"),
            err=True,
        )
        ctx.exit(1)

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # Prepare request data
        request_data = {"project_name": project_name, "instances": instances}

        if project_path:
            request_data["project_path"] = project_path
        if git_url:
            request_data["git_url"] = git_url
        if custom_commands:
            request_data["custom_commands"] = [
                cmd.strip() for cmd in custom_commands.split(",")
            ]

        # Handle port configuration
        if app_port is not None:
            # Use --app-port for simplified load balancing
            request_data["app_port"] = app_port

        if environment:
            # Parse environment variables
            env_vars = {}
            for env_var in environment.split(","):
                if "=" in env_var:
                    key, value = env_var.split("=", 1)
                    env_vars[key.strip()] = value.strip()
            request_data["environment"] = env_vars

        if command:
            request_data["command"] = command

        # Make API request
        response = client._make_request("POST", "/api/v1/scale", json=request_data)

        if verbose:
            click.echo("Scale response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success"):
                project_name = response.get("project_name", "unknown")
                created_instances = response.get("created_instances", 0)
                requested_instances = response.get("requested_instances", 0)
                containers = response.get("containers", [])

                click.echo(click.style("✓ Project scaling successful", fg="green"))
                click.echo(f"Project: {project_name}")
                click.echo(
                    f"Created: {created_instances}/{requested_instances} instances"
                )

                if containers:
                    click.echo("\nContainers created:")
                    for container in containers:
                        instance = container.get("instance", "unknown")
                        container_id = container.get("container_id", "unknown")
                        container_name = container.get("container_name", "unknown")
                        container_ports = container.get("ports", {})

                        click.echo(f"  Instance {instance}: {container_name}")
                        click.echo(f"    ID: {container_id[:12]}")
                        if container_ports:
                            click.echo(f"    Ports: {container_ports}")
                        click.echo()

                message = response.get("message", "")
                if message:
                    click.echo(f"Message: {message}")
            else:
                click.echo(click.style("✗ Project scaling failed", fg="red"))
                error_msg = response.get("message", "Unknown error")
                click.echo(f"Error: {error_msg}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)






@cli.command()
@click.option(
    "--project-name", "-n", required=True, help="Name of the project to stop"
)
@click.option("--force", "-f", is_flag=True, help="Force stop without confirmation")
@click.pass_context
def stop(ctx, project_name: str, force: bool):
    """
    Stop a running project by name.
    
    This command stops all instances of a project, whether running as individual
    containers or as a Docker Swarm service.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(api_url, timeout=timeout, verbose=verbose)

        # First, check if it's a swarm service
        try:
            swarm_response = client._make_request("GET", f"/swarm/service/{project_name}/status")
            if swarm_response.get("success"):
                # It's a swarm service, use swarm-remove
                if not force:
                    if not click.confirm(
                        f"Are you sure you want to stop swarm service '{project_name}'?"
                    ):
                        click.echo("Operation cancelled.")
                        return

                if verbose:
                    click.echo(f"Stopping swarm service: {project_name}")

                response = client._make_request("DELETE", f"/swarm/service/{project_name}")
                
                if response.get("success"):
                    click.echo(
                        click.style(
                            f"✓ Swarm service '{project_name}' stopped successfully", fg="green"
                        )
                    )
                    message = response.get("message", "")
                    if message:
                        click.echo(f"Message: {message}")
                else:
                    click.echo(click.style("✗ Failed to stop swarm service", fg="red"))
                    error_msg = response.get("message", "Unknown error")
                    click.echo(f"Error: {error_msg}")
                return
        except RacerAPIError:
            # Not a swarm service, continue to check individual containers
            pass

        # Check for individual containers with this project name
        projects_response = client._make_request("GET", "/api/v1/projects")
        if not projects_response.get("success"):
            click.echo(click.style("Failed to list projects", fg="red"), err=True)
            ctx.exit(1)

        projects = projects_response.get("projects", [])
        matching_containers = [
            p for p in projects 
            if p.get("project_name") == project_name and p.get("status") in ["running", "exited"]
        ]

        if not matching_containers:
            click.echo(
                click.style(f"No running project found with name '{project_name}'", fg="yellow")
            )
            return

        if not force:
            container_count = len(matching_containers)
            if not click.confirm(
                f"Are you sure you want to stop {container_count} container(s) for project '{project_name}'?"
            ):
                click.echo("Operation cancelled.")
                return

        # Stop all matching containers
        stopped_count = 0
        for container in matching_containers:
            container_id = container.get("container_id")
            if not container_id:
                continue

            try:
                if verbose:
                    click.echo(f"Stopping container: {container_id}")

                response = client._make_request("POST", f"/containers/{container_id}/stop")
                
                if response.get("success"):
                    stopped_count += 1
                    if verbose:
                        click.echo(f"✓ Container {container_id} stopped")
                else:
                    click.echo(
                        click.style(f"✗ Failed to stop container {container_id}", fg="red")
                    )
                    error_msg = response.get("message", "Unknown error")
                    click.echo(f"Error: {error_msg}")

            except RacerAPIError as e:
                click.echo(
                    click.style(f"Error stopping container {container_id}: {str(e)}", fg="red")
                )
            except Exception as e:
                click.echo(
                    click.style(f"Unexpected error stopping container {container_id}: {str(e)}", fg="red")
                )

        if stopped_count > 0:
            click.echo(
                click.style(
                    f"✓ Successfully stopped {stopped_count} container(s) for project '{project_name}'", 
                    fg="green"
                )
            )
        else:
            click.echo(
                click.style(f"✗ No containers were stopped for project '{project_name}'", fg="red")
            )
            ctx.exit(1)

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)




@cli.command()
@click.option(
    "--project-name",
    "-n",
    "project_name",
    required=True,
    help="Project name to rerun (will rerun all instances of this project)",
)
@click.option(
    "--custom-commands",
    "-c",
    help="Custom RUN commands to add to Dockerfile (comma-separated)",
)
@click.option(
    "--environment",
    "-e",
    help="Environment variables (format: KEY=VALUE, comma-separated)",
)
@click.option("--command", help="Override the default command to run")
@click.option(
    "--no-rebuild",
    "no_rebuild",
    is_flag=True,
    help="Skip rebuilding the Docker image (restart with existing image)",
)
@click.option(
    "--list", "list_projects", is_flag=True, help="List all running projects first"
)
@click.pass_context
def rerun(
    ctx,
    project_name: str,
    custom_commands: str,
    environment: str,
    command: str,
    no_rebuild: bool,
    list_projects: bool,
):
    """
    Rerun a project by stopping the existing container and starting a new one.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)

        # If list flag is set, show all projects
        if list_projects:
            projects_response = client._make_request("GET", "/api/v1/projects")
            if projects_response.get("success"):
                projects = projects_response.get("projects", [])
                if projects:
                    click.echo("Running projects:")
                    for project in projects:
                        click.echo(
                            f"  • {project['project_name']} (ID: {project['project_id']})"
                        )
                        click.echo(f"    Status: {project['status']}")
                        click.echo(f"    Ports: {project.get('ports', {})}")
                        click.echo()
                else:
                    click.echo("No running projects found.")
            else:
                click.echo(click.style("Failed to list projects", fg="red"), err=True)
            return

        # Find projects by name
        projects_response = client._make_request("GET", "/api/v1/projects")
        if projects_response.get("success"):
            projects = projects_response.get("projects", [])
            matching_projects = [
                p for p in projects if p["project_name"] == project_name
            ]

            if not matching_projects:
                click.echo(
                    click.style(
                        f"No running projects found with name '{project_name}'",
                        fg="red",
                    ),
                    err=True,
                )
                click.echo("Available projects:")
                for project in projects:
                    click.echo(
                        f"  • {project['project_name']} (ID: {project['project_id']})"
                    )
                return

            if len(matching_projects) == 1:
                project_id = matching_projects[0]["project_id"]
                click.echo(f"Rerunning project: {project_name}")
            else:
                # Multiple instances of the same project name - rerun all
                click.echo(
                    f"Found {len(matching_projects)} instances of project '{project_name}'. Rerunning all instances..."
                )
                for project in matching_projects:
                    click.echo(f"  • Instance {project['project_id']}")

                # Rerun all instances
                success_count = 0
                for project in matching_projects:
                    project_id = project["project_id"]
                    click.echo(f"\nRerunning instance {project_id}...")

                    # Prepare request data for this instance
                    request_data = {
                        "project_id": project_id,
                        "no_rebuild": no_rebuild,
                    }

                    if custom_commands:
                        request_data["custom_commands"] = [
                            cmd.strip() for cmd in custom_commands.split(",")
                        ]


                    if environment:
                        # Parse environment variables
                        env_vars = {}
                        for env_var in environment.split(","):
                            if "=" in env_var:
                                key, value = env_var.split("=", 1)
                                env_vars[key.strip()] = value.strip()
                        request_data["environment"] = env_vars

                    if command:
                        request_data["command"] = command

                    # Make API request for this instance
                    response = client._make_request(
                        "POST", "/project/rerun", json=request_data
                    )

                    if response.get("success"):
                        success_count += 1
                        old_container_id = response.get("old_container_id", "unknown")
                        new_container_id = response.get("new_container_id", "unknown")
                        click.echo(
                            click.style(
                                f"✓ Instance {project_id} rerun successful", fg="green"
                            )
                        )
                        if verbose:
                            click.echo(f"  Old container: {old_container_id}")
                            click.echo(f"  New container: {new_container_id}")
                    else:
                        click.echo(
                            click.style(
                                f"✗ Failed to rerun instance {project_id}: {response.get('message', 'Unknown error')}",
                                fg="red",
                            ),
                            err=True,
                        )

                click.echo(
                    f"\nRerun completed: {success_count}/{len(matching_projects)} instances successful"
                )
                return

            # Single instance - prepare request data
            request_data = {
                "project_id": project_id,
                "no_rebuild": no_rebuild,
            }

            if custom_commands:
                request_data["custom_commands"] = [
                    cmd.strip() for cmd in custom_commands.split(",")
                ]


            if environment:
                # Parse environment variables
                env_vars = {}
                for env_var in environment.split(","):
                    if "=" in env_var:
                        key, value = env_var.split("=", 1)
                        env_vars[key.strip()] = value.strip()
                request_data["environment"] = env_vars

            if command:
                request_data["command"] = command

            # Make API call
            response = client._make_request("POST", "/api/v1/rerun", json=request_data)

            if response.get("success"):
                click.echo(
                    click.style("✓ Project rerun initiated successfully", fg="green")
                )
                if verbose:
                    click.echo(f"Response: {response}")
            else:
                click.echo(
                    click.style(
                        f"✗ Failed to rerun project: {response.get('message', 'Unknown error')}",
                        fg="red",
                    ),
                    err=True,
                )
                return
        else:
            click.echo(click.style("Failed to list projects", fg="red"), err=True)
            return

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


if __name__ == "__main__":
    cli()
