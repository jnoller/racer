"""
Utilities for validating conda-project directories and git repositories.
"""

import os
import yaml
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from git import Repo, InvalidGitRepositoryError
import subprocess


class ProjectValidationError(Exception):
    """Exception raised when project validation fails."""

    pass


def validate_conda_project(project_path: str) -> Dict[str, Any]:
    """
    Validate that a directory contains a valid conda-project.

    Args:
        project_path: Path to the project directory

    Returns:
        Dictionary with validation results and project metadata

    Raises:
        ProjectValidationError: If validation fails
    """
    # Handle relative paths by resolving them from the current working directory
    if not os.path.isabs(project_path):
        project_path = os.path.abspath(project_path)

    project_path = Path(project_path).resolve()

    if not project_path.exists():
        raise ProjectValidationError(f"Project path does not exist: {project_path}")

    if not project_path.is_dir():
        raise ProjectValidationError(f"Project path is not a directory: {project_path}")

    # Check for conda-project.yml file
    conda_project_file = project_path / "conda-project.yml"
    if not conda_project_file.exists():
        raise ProjectValidationError(f"No conda-project.yml found in {project_path}")

    # Parse conda-project.yml
    try:
        with open(conda_project_file, "r") as f:
            project_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ProjectValidationError(f"Invalid YAML in conda-project.yml: {e}")
    except Exception as e:
        raise ProjectValidationError(f"Error reading conda-project.yml: {e}")

    # Validate project structure
    validation_result = {
        "valid": True,
        "project_path": str(project_path),
        "project_name": project_config.get("name", "unknown"),
        "project_version": project_config.get("version", "unknown"),
        "environments": list(project_config.get("environments", {}).keys()),
        "channels": project_config.get("channels", []),
        "dependencies": project_config.get("dependencies", {}),
        "conda_project_file": str(conda_project_file),
        "errors": [],
        "warnings": [],
    }

    # Check for required fields
    if not project_config.get("name"):
        validation_result["warnings"].append(
            "Project name not specified in conda-project.yml"
        )

    if not project_config.get("environments"):
        validation_result["warnings"].append(
            "No environments defined in conda-project.yml"
        )

    # Check for common project files
    common_files = ["README.md", "requirements.txt", "setup.py", "pyproject.toml"]
    for file_name in common_files:
        if (project_path / file_name).exists():
            validation_result["warnings"].append(
                f"Found {file_name} - consider using conda-project instead"
            )

    return validation_result


def clone_git_repository(git_url: str, target_dir: str = None) -> str:
    """
    Clone a git repository to a temporary directory.

    Args:
        git_url: Git repository URL
        target_dir: Target directory (if None, creates a temporary directory)

    Returns:
        Path to the cloned repository

    Raises:
        ProjectValidationError: If cloning fails
    """
    try:
        if target_dir is None:
            target_dir = tempfile.mkdtemp(prefix="racer_")

        # Clone the repository
        repo = Repo.clone_from(git_url, target_dir)

        return target_dir

    except Exception as e:
        raise ProjectValidationError(f"Failed to clone repository {git_url}: {e}")


def validate_git_repository(git_url: str) -> Dict[str, Any]:
    """
    Validate a git repository by cloning it and checking for conda-project.

    Args:
        git_url: Git repository URL

    Returns:
        Dictionary with validation results

    Raises:
        ProjectValidationError: If validation fails
    """
    temp_dir = None
    try:
        # Clone the repository
        temp_dir = clone_git_repository(git_url)

        # Validate the cloned project
        validation_result = validate_conda_project(temp_dir)
        validation_result["git_url"] = git_url
        validation_result["cloned_path"] = temp_dir

        return validation_result

    except Exception as e:
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
        raise ProjectValidationError(
            f"Failed to validate git repository {git_url}: {e}"
        )


def test_conda_project_install(project_path: str) -> bool:
    """
    Test if conda project install works in the project directory.

    Args:
        project_path: Path to the conda-project directory

    Returns:
        True if conda project install succeeds, False otherwise
    """
    try:
        # Run conda project install in the project directory
        result = subprocess.run(
            ["conda", "project", "install"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        return result.returncode == 0

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def cleanup_temp_directory(temp_dir: str):
    """
    Clean up a temporary directory.

    Args:
        temp_dir: Path to the temporary directory to clean up
    """
    if temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass  # Ignore cleanup errors
