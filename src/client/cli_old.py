"""
Command-line interface for the Racer client.
"""

import click
import json
import os
from typing import Optional
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
    Racer CLI - Command-line interface for the Racer deployment system.

    This tool provides commands to interact with the Racer API server
    for deploying and managing conda-project applications.
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

    This command queries the /health endpoint to verify that the API server
    is running and responding correctly.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        health_data = client.health()

        if verbose:
            click.echo("Health check response:")
            click.echo(json.dumps(health_data, indent=2))
        else:
            # Simple status display
            status = health_data.get("status", "unknown")
            service = health_data.get("service", "unknown")
            version = health_data.get("version", "unknown")
            timestamp = health_data.get("timestamp", "unknown")

            if status == "healthy":
                click.echo(
                    click.style(f"✓ {service} v{version} is healthy", fg="green")
                )
                click.echo(f"  Timestamp: {timestamp}")
            else:
                click.echo(click.style(f"✗ {service} v{version} is {status}", fg="red"))
                click.echo(f"  Timestamp: {timestamp}")

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

    This command queries the /liveness endpoint to verify that the API server
    is alive and should continue running (used by container orchestrators).
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        liveness_data = client.liveness()

        if verbose:
            click.echo("Liveness check response:")
            click.echo(json.dumps(liveness_data, indent=2))
        else:
            # Simple status display
            alive = liveness_data.get("alive", False)
            uptime = liveness_data.get("uptime", "unknown")
            timestamp = liveness_data.get("timestamp", "unknown")

            if alive:
                click.echo(click.style("✓ Server is alive", fg="green"))
                click.echo(f"  Uptime: {uptime}")
                click.echo(f"  Timestamp: {timestamp}")
            else:
                click.echo(click.style("✗ Server is not alive", fg="red"))
                click.echo(f"  Timestamp: {timestamp}")

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

    This command queries the /ready endpoint to verify that the API server
    is ready to accept traffic (checks dependencies like database, Docker, etc.).
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        readiness_data = client.readiness()

        if verbose:
            click.echo("Readiness check response:")
            click.echo(json.dumps(readiness_data, indent=2))
        else:
            # Simple status display
            ready = readiness_data.get("ready", False)
            checks = readiness_data.get("checks", {})
            timestamp = readiness_data.get("timestamp", "unknown")

            if ready:
                click.echo(click.style("✓ Server is ready", fg="green"))
                click.echo(f"  Timestamp: {timestamp}")

                # Show individual checks
                if checks:
                    click.echo("  Dependency checks:")
                    for check, status in checks.items():
                        status_icon = "✓" if status == "ok" else "✗"
                        status_color = "green" if status == "ok" else "red"
                        click.echo(f"    {status_icon} {check}: {status}")
            else:
                click.echo(click.style("✗ Server is not ready", fg="red"))
                click.echo(f"  Timestamp: {timestamp}")

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

    This command queries the root endpoint to get API information and
    available endpoints.
    """
    api_url = ctx.obj["api_url"]
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]

    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        info_data = client.info()

        if verbose:
            click.echo("API information response:")
            click.echo(json.dumps(info_data, indent=2))
        else:
            # Simple info display
            message = info_data.get("message", "Unknown")
            version = info_data.get("version", "unknown")

            click.echo(click.style(f"{message} v{version}", fg="blue"))

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


if __name__ == "__main__":
    cli()
