"""
RacerCTL - Admin CLI for the Racer deployment system.
"""

import click
import json
import os
from api import RacerAPIClient, RacerAPIError


# Global configuration
API_URL = os.getenv("RACER_API_URL", "http://localhost:8000")


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
@click.pass_context
def health(ctx):
    """
    Check the health status of the Racer API server.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client.health()

        if verbose:
            click.echo("Health response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("status") == "healthy":
                click.echo(click.style("✓ API is healthy", fg="green"))
                click.echo(f"Status: {response.get('status')}")
                click.echo(f"Timestamp: {response.get('timestamp')}")
            else:
                click.echo(click.style("✗ API is not healthy", fg="red"))
                click.echo(f"Status: {response.get('status')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
def liveness(ctx):
    """
    Check the liveness status of the Racer API server.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client.liveness()

        if verbose:
            click.echo("Liveness response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("status") == "alive":
                click.echo(click.style("✓ API is alive", fg="green"))
                click.echo(f"Status: {response.get('status')}")
                click.echo(f"Timestamp: {response.get('timestamp')}")
            else:
                click.echo(click.style("✗ API is not alive", fg="red"))
                click.echo(f"Status: {response.get('status')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
def readiness(ctx):
    """
    Check the readiness status of the Racer API server.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client.readiness()

        if verbose:
            click.echo("Readiness response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get("status") == "ready":
                click.echo(click.style("✓ API is ready", fg="green"))
                click.echo(f"Status: {response.get('status')}")
                click.echo(f"Timestamp: {response.get('timestamp')}")
            else:
                click.echo(click.style("✗ API is not ready", fg="red"))
                click.echo(f"Status: {response.get('status')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
def info(ctx):
    """
    Get basic information about the Racer API server.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        response = client.info()

        if verbose:
            click.echo("Info response:")
            click.echo(json.dumps(response, indent=2))
        else:
            click.echo(f"Service: {response.get('service', 'unknown')}")
            click.echo(f"Version: {response.get('version', 'unknown')}")
            click.echo(f"Uptime: {response.get('uptime', 'unknown')}")
            click.echo(f"Status: {response.get('status', 'unknown')}")

    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg="red"), err=True)
        ctx.exit(1)


@cli.group()
def containers():
    """Manage Docker containers."""
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
        response = client._make_request("GET", "/containers")

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
        response = client._make_request("GET", f"/containers/{container_id}/status")

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
        response = client._make_request("POST", f"/containers/{container_id}/stop")

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
        response = client._make_request("DELETE", f"/containers/{container_id}")

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
        response = client._make_request("POST", "/containers/cleanup")

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


if __name__ == "__main__":
    cli()
