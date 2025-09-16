"""
RacerCTL - Admin CLI for the Racer deployment system.
"""

import click
import json
import os
import subprocess
import signal
import time
import psutil
from api import RacerAPIClient, RacerAPIError


# Global configuration
API_URL = os.getenv("RACER_API_URL", "http://localhost:8001")


@click.group()
@click.version_option(version="0.1.0", prog_name="racerctl")
@click.option(
    "--api-url", default=API_URL, help="Racer API server URL", envvar="RACER_API_URL"
)
@click.option("--timeout", default=30, type=int, help="Request timeout in seconds")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, api_url: str, timeout: int, verbose: bool):
    """
    RacerCTL - Admin CLI for the Racer deployment system.

    This tool provides administrative commands to manage the Racer API server
    and Docker containers for conda-project applications.
    """
    # Ensure that ctx.obj exists and is a dict
    ctx.ensure_object(dict)

    # Store configuration in context
    ctx.obj["api_url"] = api_url
    ctx.obj["timeout"] = timeout
    ctx.obj["verbose"] = verbose

    if verbose:
        click.echo(f"Using API URL: {api_url}")
        click.echo(f"Request timeout: {timeout}s")


@cli.command()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def status(ctx, verbose):
    """
    Get comprehensive status information about the Racer API server.

    This command consolidates health, liveness, readiness, and info checks
    into a single comprehensive status report.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        
        # Collect all status information
        health_data = client.health()
        liveness_data = client.liveness()
        readiness_data = client.readiness()
        info_data = client.info()

        if verbose:
            click.echo("Complete status response:")
            click.echo("Health: " + json.dumps(health_data, indent=2))
            click.echo("Liveness: " + json.dumps(liveness_data, indent=2))
            click.echo("Readiness: " + json.dumps(readiness_data, indent=2))
            click.echo("Info: " + json.dumps(info_data, indent=2))
        else:
            # Comprehensive status display
            click.echo(click.style("🔍 Racer API Server Status", fg="blue", bold=True))
            click.echo()

            # Server Information
            service = health_data.get("service", "unknown")
            version = health_data.get("version", "unknown")
            click.echo(f"Service: {service} v{version}")
            click.echo(f"API URL: {api_url}")
            click.echo()

            # Health Status
            health_status = health_data.get("status", "unknown")
            health_timestamp = health_data.get("timestamp", "unknown")
            if health_status == "healthy":
                click.echo(click.style("✓ Health: Healthy", fg="green"))
            else:
                click.echo(click.style(f"✗ Health: {health_status}", fg="red"))
            click.echo(f"  Checked: {health_timestamp}")
            click.echo()

            # Liveness Status
            alive = liveness_data.get("alive", False)
            liveness_timestamp = liveness_data.get("timestamp", "unknown")
            if alive:
                click.echo(click.style("✓ Liveness: Alive", fg="green"))
            else:
                click.echo(click.style("✗ Liveness: Not alive", fg="red"))
            click.echo(f"  Checked: {liveness_timestamp}")
            click.echo()

            # Readiness Status
            ready = readiness_data.get("ready", False)
            readiness_timestamp = readiness_data.get("timestamp", "unknown")
            if ready:
                click.echo(click.style("✓ Readiness: Ready", fg="green"))
            else:
                click.echo(click.style("✗ Readiness: Not ready", fg="red"))
            click.echo(f"  Checked: {readiness_timestamp}")
            click.echo()

            # Overall Status Summary
            all_healthy = (health_status == "healthy" and alive and ready)
            if all_healthy:
                click.echo(click.style("🎉 Overall Status: All systems operational", fg="green", bold=True))
            else:
                click.echo(click.style("⚠️  Overall Status: Issues detected", fg="yellow", bold=True))
            click.echo()

            # API Information
            message = info_data.get("message", "Unknown")
            click.echo(f"Description: {message}")
            
            # Show available endpoints
            endpoints = {
                k: v for k, v in info_data.items() if k not in ["message", "version"]
            }
            if endpoints:
                click.echo("Available endpoints:")
                for endpoint, path in endpoints.items():
                    click.echo(f"  {endpoint}: {path}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.group()
def server():
    """Manage the Racer backend server."""
    pass


@server.command("start")
@click.option("--port", "-p", default=8001, help="Port to run the server on")
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option(
    "--reload", is_flag=True, default=True, help="Enable auto-reload for development"
)
@click.option(
    "--foreground",
    "-f",
    is_flag=True,
    help="Run server in foreground (default is background)",
)
@click.option("--env", default="racer-dev", help="Conda environment to use")
@click.pass_context
def start_server(ctx, port: int, host: str, reload: bool, foreground: bool, env: str):
    """
    Start the Racer backend server.

    This command starts the FastAPI backend server using uvicorn.
    By default, it runs in background mode with auto-reload enabled.
    Use --foreground to run in the foreground.
    """
    verbose = ctx.obj["verbose"]

    # Check if server is already running
    if is_server_running(port):
        click.echo(
            click.style(f"⚠️  Server is already running on port {port}", fg="yellow")
        )
        if not click.confirm("Do you want to stop it and start a new one?"):
            click.echo("Aborted.")
            return
        stop_server_process(port)
        time.sleep(2)

    # Build the uvicorn command
    cmd = [
        "conda",
        "run",
        "-n",
        env,
        "uvicorn",
        "main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]

    if reload:
        cmd.append("--reload")

    if verbose:
        click.echo(f"Starting server with command: {' '.join(cmd)}")

    try:
        if not foreground:  # Default to background mode
            # Run in background
            process = subprocess.Popen(
                cmd,
                cwd="src/backend",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid if os.name != "nt" else None,
            )

            # Wait a moment to check if it started successfully
            time.sleep(3)

            if process.poll() is None:
                click.echo(
                    click.style(
                        f"✓ Server started in background on {host}:{port}", fg="green"
                    )
                )
                click.echo(f"Process ID: {process.pid}")
                click.echo(f"To stop: racerctl server stop --port {port}")
            else:
                stdout, stderr = process.communicate()
                click.echo(click.style("✗ Failed to start server", fg="red"))
                click.echo(f"Error: {stderr.decode()}")
                ctx.exit(1)
        else:
            # Run in foreground
            click.echo(click.style(f"Starting server on {host}:{port}...", fg="blue"))
            click.echo("Press Ctrl+C to stop the server")
            subprocess.run(cmd, cwd="src/backend")

    except KeyboardInterrupt:
        click.echo("\nServer stopped by user")
    except Exception as e:
        click.echo(click.style(f"Error starting server: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@server.command("stop")
@click.option("--port", "-p", default=8001, help="Port of the server to stop")
@click.option("--force", "-f", is_flag=True, help="Force stop the server")
@click.pass_context
def stop_server(ctx, port: int, force: bool):
    """
    Stop the Racer backend server.

    This command stops the running FastAPI backend server.
    """
    verbose = ctx.obj["verbose"]

    if not is_server_running(port):
        click.echo(
            click.style(f"⚠️  No server found running on port {port}", fg="yellow")
        )
        return

    try:
        if stop_server_process(port, force):
            click.echo(click.style(f"✓ Server stopped on port {port}", fg="green"))
        else:
            click.echo(click.style("✗ Failed to stop server", fg="red"))
            if not force:
                click.echo("Try using --force to force stop the server")
            ctx.exit(1)

    except Exception as e:
        click.echo(click.style(f"Error stopping server: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@server.command("status")
@click.option("--port", "-p", default=8001, help="Port to check")
@click.pass_context
def server_status(ctx, port: int):
    """
    Check the status of the Racer backend server.

    This command checks if the server is running and provides status information.
    """
    verbose = ctx.obj["verbose"]

    # Check if process is running
    if is_server_running(port):
        click.echo(click.style(f"✓ Server is running on port {port}", fg="green"))

        # Try to get API health
        try:
            api_url = f"http://localhost:{port}"
            client = RacerAPIClient(base_url=api_url, timeout=5)
            health_data = client.health()

            status = health_data.get("status", "unknown")
            service = health_data.get("service", "unknown")
            version = health_data.get("version", "unknown")

            click.echo(f"  Service: {service} v{version}")
            click.echo(f"  Status: {status}")
            click.echo(f"  API URL: {api_url}")

            if verbose:
                click.echo("  Full health data:")
                click.echo(json.dumps(health_data, indent=2))

        except Exception as e:
            click.echo(
                click.style(
                    f"  ⚠️  Server is running but API is not responding: {str(e)}",
                    fg="yellow",
                )
            )
    else:
        click.echo(click.style(f"✗ Server is not running on port {port}", fg="red"))
        click.echo(f"  To start: racerctl server start --port {port}")


@server.command("restart")
@click.option("--port", "-p", default=8001, help="Port of the server to restart")
@click.option("--host", default="0.0.0.0", help="Host to bind the server to")
@click.option(
    "--reload", is_flag=True, default=True, help="Enable auto-reload for development"
)
@click.option(
    "--foreground",
    "-f",
    is_flag=True,
    help="Run server in foreground (default is background)",
)
@click.option("--env", default="racer-dev", help="Conda environment to use")
@click.pass_context
def restart_server(ctx, port: int, host: str, reload: bool, foreground: bool, env: str):
    """
    Restart the Racer backend server.

    This command stops the current server and starts a new one.
    By default, restarts in background mode.
    """
    click.echo(click.style("Restarting server...", fg="blue"))

    # Stop the server
    if is_server_running(port):
        click.echo("Stopping current server...")
        stop_server_process(port)
        time.sleep(2)

    # Start the server
    click.echo("Starting new server...")
    ctx.invoke(
        start_server,
        port=port,
        host=host,
        reload=reload,
        foreground=foreground,
        env=env,
    )


def is_server_running(port: int) -> bool:
    """Check if a server is running on the specified port."""
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if (
                    cmdline
                    and "uvicorn" in " ".join(cmdline)
                    and f"--port {port}" in " ".join(cmdline)
                ):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception:
        return False


def stop_server_process(port: int, force: bool = False) -> bool:
    """Stop the server process running on the specified port."""
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = proc.info["cmdline"]
                if (
                    cmdline
                    and "uvicorn" in " ".join(cmdline)
                    and f"--port {port}" in " ".join(cmdline)
                ):
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()

                    # Wait for process to stop
                    try:
                        proc.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        if force:
                            proc.kill()
                        else:
                            return False
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False
    except Exception:
        return False


@cli.group()
def containers():
    """Manage Docker containers."""
    pass


@cli.group()
def swarm():
    """Manage Docker Swarm services."""
    pass


@containers.command("list")
@click.pass_context
def list_containers(ctx):
    """
    List all tracked containers.

    Shows all containers that are currently being managed by the Racer system.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client._make_request("GET", "/admin/containers")

        if verbose:
            click.echo("Containers response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                containers = response.get("containers", [])
                count = response.get("count", 0)

                if count == 0:
                    click.echo("No containers found.")
                else:
                    click.echo(f"Found {count} container(s):")
                    click.echo()

                    for container in containers:
                        status_color = (
                            "green"
                            if container.get("status") == "running"
                            else "yellow"
                        )
                        click.echo(
                            click.style(
                                f"• {container.get('container_name', 'unknown')}",
                                fg=status_color,
                            )
                        )
                        click.echo(f"  ID: {container.get('container_id', 'unknown')}")
                        click.echo(
                            f"  Project: {container.get('project_name', 'unknown')}"
                        )
                        click.echo(f"  Status: {container.get('status', 'unknown')}")
                        click.echo(f"  Image: {container.get('image', 'unknown')}")
                        click.echo(
                            f"  Started: {container.get('started_at', 'unknown')}"
                        )

                        # Show port mappings
                        ports = container.get("ports", {})
                        if ports:
                            click.echo("  Ports:")
                            for container_port, host_port in ports.items():
                                click.echo(f"    {host_port} -> {container_port}")
                        click.echo()
            else:
                click.echo(click.style("✗ Failed to list containers", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@containers.command("status")
@click.argument("container_id")
@click.pass_context
def container_status(ctx, container_id: str):
    """
    Get the status of a specific container.

    Args:
        container_id: ID of the container to check
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client._make_request(
            "GET", f"/admin/containers/{container_id}/status"
        )

        if verbose:
            click.echo("Container status response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                status_color = (
                    "green" if response.get("status") == "running" else "yellow"
                )
                click.echo(click.style("✓ Container Status", fg=status_color))
                click.echo(f"Name: {response.get('container_name', 'unknown')}")
                click.echo(f"ID: {response.get('container_id', 'unknown')}")
                click.echo(f"Status: {response.get('status', 'unknown')}")
                click.echo(f"Image: {response.get('image', 'unknown')}")
                click.echo(f"Started: {response.get('started_at', 'unknown')}")

                if response.get("stopped_at"):
                    click.echo(f"Stopped: {response.get('stopped_at')}")

                # Show port mappings
                ports = response.get("ports", {})
                if ports:
                    click.echo("Ports:")
                    for container_port, host_port in ports.items():
                        click.echo(f"  {host_port} -> {container_port}")
            else:
                click.echo(click.style("✗ Failed to get container status", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@containers.command("logs")
@click.argument("container_id")
@click.option("--tail", "-t", default=100, help="Number of lines to show")
@click.pass_context
def container_logs(ctx, container_id: str, tail: int):
    """
    Get logs from a specific container.

    Args:
        container_id: ID of the container
        tail: Number of lines to show
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client._make_request(
            "GET", f"/containers/{container_id}/logs?tail={tail}"
        )

        if verbose:
            click.echo("Container logs response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                logs = response.get("logs", "")
                if logs:
                    click.echo(f"Logs for container {container_id}:")
                    click.echo("-" * 50)
                    click.echo(logs)
                else:
                    click.echo("No logs available for this container.")
            else:
                click.echo(click.style("✗ Failed to get container logs", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@containers.command("stop")
@click.argument("container_id")
@click.pass_context
def stop_container(ctx, container_id: str):
    """
    Stop a running container.

    Args:
        container_id: ID of the container to stop
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client._make_request(
            "POST", f"/admin/containers/{container_id}/stop"
        )

        if verbose:
            click.echo("Stop container response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                click.echo(click.style("✓ Container stopped successfully", fg="green"))
                click.echo(f"Container ID: {response.get('container_id', 'unknown')}")
                click.echo(f"Message: {response.get('message', '')}")
            else:
                click.echo(click.style("✗ Failed to stop container", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@containers.command("remove")
@click.argument("container_id")
@click.pass_context
def remove_container(ctx, container_id: str):
    """
    Remove a container.

    Args:
        container_id: ID of the container to remove
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client._make_request("DELETE", f"/admin/containers/{container_id}")

        if verbose:
            click.echo("Remove container response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                click.echo(click.style("✓ Container removed successfully", fg="green"))
                click.echo(f"Container ID: {response.get('container_id', 'unknown')}")
                click.echo(f"Message: {response.get('message', '')}")
            else:
                click.echo(click.style("✗ Failed to remove container", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@containers.command("cleanup")
@click.pass_context
def cleanup_containers(ctx):
    """
    Clean up stopped containers.

    Removes all containers that have stopped or exited.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client._make_request("POST", "/admin/containers/cleanup")

        if verbose:
            click.echo("Cleanup response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("success", False):
                cleaned_up = response.get("cleaned_up", 0)
                click.echo(click.style("✓ Cleanup completed", fg="green"))
                click.echo(f"Removed {cleaned_up} stopped container(s)")
                click.echo(f"Message: {response.get('message', '')}")
            else:
                click.echo(click.style("✗ Failed to cleanup containers", fg="red"))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@swarm.command("status")
@click.option("--project-name", "-n", help="Name of the project to check status")
@click.pass_context
def swarm_status(ctx, project_name: str):
    """
    Check the status of Docker Swarm services.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(api_url, timeout=timeout, verbose=verbose)

        if project_name:
            # Get status for specific service
            response = client._make_request(
                "GET", f"/admin/swarm/service/{project_name}/status"
            )

            if response.get("success"):
                click.echo(
                    click.style(f"✓ Service status for {project_name}", fg="green")
                )
                click.echo(f"Service ID: {response.get('service_id', 'unknown')}")
                click.echo(
                    f"Replicas: {response.get('running_replicas', 0)}/{response.get('replicas', 0)}"
                )
                click.echo(f"Status: {response.get('status', 'unknown')}")
                click.echo(f"Image: {response.get('image', 'unknown')}")

                ports = response.get("ports", {})
                if ports:
                    click.echo("Ports:")
                    for port, mapping in ports.items():
                        click.echo(f"  {port} -> {mapping}")

                message = response.get("message", "")
                if message:
                    click.echo(f"Message: {message}")
            else:
                click.echo(click.style("✗ Failed to get service status", fg="red"))
                error_msg = response.get("message", "Unknown error")
                click.echo(f"Error: {error_msg}")
        else:
            # List all services
            response = client._make_request("GET", "/admin/swarm/services")

            if response.get("success"):
                services = response.get("services", [])
                if services:
                    click.echo(click.style("✓ Docker Swarm Services", fg="green"))
                    click.echo()
                    for service in services:
                        click.echo(f"Service: {service.get('service_name', 'unknown')}")
                        click.echo(f"  ID: {service.get('service_id', 'unknown')[:12]}")
                        click.echo(
                            f"  Replicas: {service.get('running_replicas', 0)}/{service.get('replicas', 0)}"
                        )
                        click.echo(f"  Status: {service.get('status', 'unknown')}")
                        click.echo(f"  Image: {service.get('image', 'unknown')}")

                        ports = service.get("ports", {})
                        if ports:
                            click.echo("  Ports:")
                            for port, mapping in ports.items():
                                click.echo(f"    {port} -> {mapping}")
                        click.echo()
                else:
                    click.echo("No Docker Swarm services found.")

                message = response.get("message", "")
                if message:
                    click.echo(f"Message: {message}")
            else:
                click.echo(click.style("✗ Failed to list services", fg="red"))
                error_msg = response.get("message", "Unknown error")
                click.echo(f"Error: {error_msg}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@swarm.command("logs")
@click.option(
    "--project-name", "-n", required=True, help="Name of the project to get logs from"
)
@click.option("--tail", "-t", default=100, help="Number of log lines to retrieve")
@click.pass_context
def swarm_logs(ctx, project_name: str, tail: int):
    """
    Get logs from a Docker Swarm service.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(api_url, timeout=timeout, verbose=verbose)

        if verbose:
            click.echo(f"Getting logs for service: {project_name}")
            click.echo(f"Tail: {tail} lines")

        # Make API call
        response = client._make_request(
            "GET", f"/admin/swarm/service/{project_name}/logs?tail={tail}"
        )

        if response.get("success"):
            logs = response.get("logs", "")
            if logs:
                click.echo(f"Logs for service {project_name}:")
                click.echo("-" * 50)
                click.echo(logs)
            else:
                click.echo("No logs available for this service.")
        else:
            click.echo(click.style("✗ Failed to get service logs", fg="red"))
            error_msg = response.get("message", "Unknown error")
            click.echo(f"Error: {error_msg}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@swarm.command("remove")
@click.option(
    "--project-name", "-n", required=True, help="Name of the project to remove"
)
@click.option("--force", "-f", is_flag=True, help="Force removal without confirmation")
@click.pass_context
def swarm_remove(ctx, project_name: str, force: bool):
    """
    Remove a Docker Swarm service.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        if not force:
            if not click.confirm(
                f"Are you sure you want to remove service '{project_name}'?"
            ):
                click.echo("Operation cancelled.")
                return

        client = RacerAPIClient(api_url, timeout=timeout, verbose=verbose)

        if verbose:
            click.echo(f"Removing service: {project_name}")

        # Make API call
        response = client._make_request(
            "DELETE", f"/admin/swarm/service/{project_name}"
        )

        if response.get("success"):
            click.echo(
                click.style(
                    f"✓ Service '{project_name}' removed successfully", fg="green"
                )
            )
            message = response.get("message", "")
            if message:
                click.echo(f"Message: {message}")
        else:
            click.echo(click.style("✗ Failed to remove service", fg="red"))
            error_msg = response.get("message", "Unknown error")
            click.echo(f"Error: {error_msg}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


if __name__ == "__main__":
    cli()
