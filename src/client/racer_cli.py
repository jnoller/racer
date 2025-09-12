"""
Racer CLI - User-facing commands for running conda-projects.
"""

import click
import json
import os
from typing import Optional
from api import RacerAPIClient, RacerAPIError


@click.group()
@click.option('--api-url', default='http://localhost:8000',
              help='Racer API server URL')
@click.option('--timeout', default=30, type=int,
              help='Request timeout in seconds')
@click.option('-v', '--verbose', is_flag=True,
              help='Enable verbose output')
@click.pass_context
def cli(ctx, api_url: str, timeout: int, verbose: bool):
    """
    Racer - Rapid deployment system for conda-projects.
    
    This tool provides user-facing commands to run and manage your conda-projects
    in Docker containers with a single command.
    """
    ctx.ensure_object(dict)
    ctx.obj['api_url'] = api_url
    ctx.obj['timeout'] = timeout
    ctx.obj['verbose'] = verbose


@cli.command()
@click.option('--path', '-p', 'project_path', 
              help='Path to local conda-project directory')
@click.option('--git', '-g', 'git_url', 
              help='Git repository URL containing conda-project')
@click.option('--custom-commands', '-c', 
              help='Custom RUN commands to add to Dockerfile (comma-separated)')
@click.option('--ports', 
              help='Port mappings (format: host:container,host:container)')
@click.option('--env', '-e', 'environment', 
              help='Environment variables (format: KEY=VALUE,KEY=VALUE)')
@click.option('--command', 
              help='Override command to run in container')
@click.option('--build-only', is_flag=True, 
              help='Only build the Docker image, do not run')
@click.pass_context
def run(ctx, project_path: str, git_url: str, custom_commands: str, ports: str, 
        environment: str, command: str, build_only: bool):
    """
    Run a conda-project by building and running a Docker container.
    
    This command builds a Docker image from a conda-project and runs it in a container.
    """
    api_url = ctx.obj['api_url']
    timeout = ctx.obj['timeout']
    verbose = ctx.obj['verbose']
    
    if not project_path and not git_url:
        click.echo(click.style("Error: Either --path or --git must be specified", fg='red'), err=True)
        ctx.exit(1)
    
    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        
        # Prepare request data
        request_data = {}
        if project_path:
            request_data['project_path'] = project_path
        if git_url:
            request_data['git_url'] = git_url
        if custom_commands:
            request_data['custom_commands'] = [cmd.strip() for cmd in custom_commands.split(',')]
        if ports:
            # Parse port mappings
            port_mappings = {}
            for port_mapping in ports.split(','):
                if ':' in port_mapping:
                    host_port, container_port = port_mapping.split(':')
                    port_mappings[f"{container_port}/tcp"] = int(host_port)
                else:
                    port_mappings[f"{port_mapping}/tcp"] = int(port_mapping)
            request_data['ports'] = port_mappings
        if environment:
            # Parse environment variables
            env_vars = {}
            for env_var in environment.split(','):
                if '=' in env_var:
                    key, value = env_var.split('=', 1)
                    env_vars[key] = value
            request_data['environment'] = env_vars
        if command:
            request_data['command'] = command
        
        if build_only:
            # Use the old /run endpoint for build-only
            response = client._make_request('POST', '/run', json=request_data)
            
            if verbose:
                click.echo("Build preparation response:")
                click.echo(json.dumps(response, indent=2))
            else:
                if response.get('success', False):
                    click.echo(click.style("✓ Project prepared for building", fg='green'))
                    click.echo(f"Project: {response.get('project_name', 'unknown')}")
                    click.echo(f"Dockerfile: {response.get('dockerfile_path', 'unknown')}")
                    
                    # Show build instructions
                    instructions = response.get('instructions', {})
                    if instructions:
                        click.echo("\nBuild command:")
                        click.echo(f"  {instructions.get('build', 'N/A')}")
                else:
                    click.echo(click.style("✗ Failed to prepare project for building", fg='red'))
        else:
            # Use the new /containers/run endpoint for actual container execution
            response = client._make_request('POST', '/containers/run', json=request_data)
            
            if verbose:
                click.echo("Container run response:")
                click.echo(json.dumps(response, indent=2))
            else:
                if response.get('success', False):
                    click.echo(click.style("✓ Container started successfully", fg='green'))
                    click.echo(f"Container ID: {response.get('container_id', 'unknown')}")
                    click.echo(f"Container Name: {response.get('container_name', 'unknown')}")
                    click.echo(f"Status: {response.get('status', 'unknown')}")
                    
                    # Show port mappings
                    port_mappings = response.get('ports', {})
                    if port_mappings:
                        click.echo("Port mappings:")
                        for container_port, host_port in port_mappings.items():
                            click.echo(f"  {host_port} -> {container_port}")
                    
                    click.echo(f"\nMessage: {response.get('message', '')}")
                    click.echo("\nUse 'racerctl containers list' to see all running containers")
                    click.echo("Use 'racerctl containers logs <container_id>' to view logs")
                else:
                    click.echo(click.style("✗ Failed to start container", fg='red'))
                    click.echo(f"Error: {response.get('error', 'Unknown error')}")
                
    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)


@cli.command()
@click.option('--path', '-p', 'project_path', 
              help='Path to local conda-project directory')
@click.option('--git', '-g', 'git_url', 
              help='Git repository URL containing conda-project')
@click.pass_context
def validate(ctx, project_path: str, git_url: str):
    """
    Validate a conda-project directory or git repository.
    """
    api_url = ctx.obj['api_url']
    timeout = ctx.obj['timeout']
    verbose = ctx.obj['verbose']
    
    if not project_path and not git_url:
        click.echo(click.style("Error: Either --path or --git must be specified", fg='red'), err=True)
        ctx.exit(1)
    
    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        
        # Prepare request data
        request_data = {}
        if project_path:
            request_data['project_path'] = project_path
        if git_url:
            request_data['git_url'] = git_url
        
        # Make API request
        response = client._make_request('POST', '/validate', json=request_data)
        
        if verbose:
            click.echo("Validation response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get('valid', False):
                click.echo(click.style("✓ Project is valid", fg='green'))
                click.echo(f"Project: {response.get('project_name', 'unknown')}")
                click.echo(f"Version: {response.get('project_version', 'unknown')}")
                click.echo(f"Environments: {', '.join(response.get('environments', []))}")
                click.echo(f"Channels: {', '.join(response.get('channels', []))}")
                
                # Show warnings if any
                warnings = response.get('warnings', [])
                if warnings:
                    click.echo("\nWarnings:")
                    for warning in warnings:
                        click.echo(click.style(f"  ⚠ {warning}", fg='yellow'))
            else:
                click.echo(click.style("✗ Project is invalid", fg='red'))
                errors = response.get('errors', [])
                for error in errors:
                    click.echo(click.style(f"  ✗ {error}", fg='red'))
                
    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)


@cli.command()
@click.option('--path', '-p', 'project_path', 
              help='Path to local conda-project directory')
@click.option('--git', '-g', 'git_url', 
              help='Git repository URL containing conda-project')
@click.option('--custom-commands', '-c', 
              help='Custom RUN commands to add to Dockerfile (comma-separated)')
@click.pass_context
def dockerfile(ctx, project_path: str, git_url: str, custom_commands: str):
    """
    Generate a Dockerfile for a conda-project.
    """
    api_url = ctx.obj['api_url']
    timeout = ctx.obj['timeout']
    verbose = ctx.obj['verbose']
    
    if not project_path and not git_url:
        click.echo(click.style("Error: Either --path or --git must be specified", fg='red'), err=True)
        ctx.exit(1)
    
    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        
        # Prepare request data
        request_data = {}
        if project_path:
            request_data['project_path'] = project_path
        if git_url:
            request_data['git_url'] = git_url
        if custom_commands:
            request_data['custom_commands'] = [cmd.strip() for cmd in custom_commands.split(',')]
        
        # Make API request
        response = client._make_request('POST', '/dockerfile', json=request_data)
        
        if verbose:
            click.echo("Dockerfile generation response:")
            click.echo(json.dumps(response, indent=2))
        else:
            if response.get('success', False):
                click.echo(click.style("✓ Dockerfile generated successfully", fg='green'))
                click.echo(f"Project: {response.get('project_name', 'unknown')}")
                click.echo(f"Dockerfile: {response.get('dockerfile_path', 'unknown')}")
                
                # Show Dockerfile content
                dockerfile_content = response.get('dockerfile_content', '')
                if dockerfile_content:
                    click.echo("\nDockerfile content:")
                    click.echo("-" * 50)
                    click.echo(dockerfile_content)
            else:
                click.echo(click.style("✗ Failed to generate Dockerfile", fg='red'))
                click.echo(f"Error: {response.get('error', 'Unknown error')}")
                
    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """
    Check the status of the Racer API server.
    """
    api_url = ctx.obj['api_url']
    timeout = ctx.obj['timeout']
    verbose = ctx.obj['verbose']
    
    try:
        client = RacerAPIClient(base_url=api_url, timeout=timeout)
        
        # Get health status
        health_response = client._make_request('GET', '/health')
        info_response = client._make_request('GET', '/')
        
        if verbose:
            click.echo("Health response:")
            click.echo(json.dumps(health_response, indent=2))
            click.echo("\nInfo response:")
            click.echo(json.dumps(info_response, indent=2))
        else:
            if health_response.get('status') == 'healthy':
                click.echo(click.style("✓ Racer API is healthy", fg='green'))
                click.echo(f"Version: {info_response.get('version', 'unknown')}")
                click.echo(f"Service: {info_response.get('service', 'unknown')}")
                click.echo(f"Uptime: {info_response.get('uptime', 'unknown')}")
            else:
                click.echo(click.style("✗ Racer API is not healthy", fg='red'))
                click.echo(f"Status: {health_response.get('status', 'unknown')}")
                
    except RacerAPIError as e:
        click.echo(click.style(f"Error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {str(e)}", fg='red'), err=True)
        ctx.exit(1)


if __name__ == '__main__':
    cli()
