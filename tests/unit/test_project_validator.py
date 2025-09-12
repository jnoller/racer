"""
Unit tests for project validator.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from src.backend.project_validator import (
    validate_conda_project,
    validate_git_repository,
    cleanup_temp_directory
)


class TestProjectValidator:
    """Test cases for project validation functions."""
    
    def test_validate_conda_project_success(self, test_project_dir, sample_conda_project_yml, sample_environment_yml):
        """Test successful conda-project validation."""
        result = validate_conda_project(test_project_dir)
        
        assert result["valid"] is True
        assert result["project_name"] == "test-project"
        assert result["project_version"] is None
        assert "default" in result["environments"]
        assert "conda-forge" in result["channels"]
        assert len(result["errors"]) == 0
    
    def test_validate_conda_project_missing_conda_project_yml(self, temp_dir):
        """Test validation with missing conda-project.yml."""
        result = validate_conda_project(temp_dir)
        
        assert result["valid"] is False
        assert "conda-project.yml not found" in result["errors"][0]
    
    def test_validate_conda_project_invalid_yaml(self, temp_dir):
        """Test validation with invalid YAML."""
        # Create invalid YAML file
        invalid_yml = Path(temp_dir) / "conda-project.yml"
        invalid_yml.write_text("invalid: yaml: content: [")
        
        result = validate_conda_project(temp_dir)
        
        assert result["valid"] is False
        assert "Failed to parse conda-project.yml" in result["errors"][0]
    
    def test_validate_conda_project_missing_environment_yml(self, temp_dir):
        """Test validation with missing environment.yml."""
        # Create conda-project.yml but no environment.yml
        conda_project_yml = Path(temp_dir) / "conda-project.yml"
        conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
""")
        
        result = validate_conda_project(temp_dir)
        
        assert result["valid"] is False
        assert "environment.yml not found" in result["errors"][0]
    
    def test_validate_conda_project_missing_commands(self, temp_dir):
        """Test validation with missing commands section."""
        # Create conda-project.yml without commands
        conda_project_yml = Path(temp_dir) / "conda-project.yml"
        conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
""")
        
        # Create environment.yml
        environment_yml = Path(temp_dir) / "environment.yml"
        environment_yml.write_text("""name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
variables: {}
""")
        
        result = validate_conda_project(temp_dir)
        
        assert result["valid"] is True
        assert "No commands defined" in result["warnings"][0]
    
    @patch('src.backend.project_validator.git.Repo')
    def test_validate_git_repository_success(self, mock_repo_class, temp_dir, sample_conda_project_yml, sample_environment_yml):
        """Test successful git repository validation."""
        # Mock git repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.clone_from.return_value = mock_repo
        
        # Mock cloned repository contents
        with patch('src.backend.project_validator.os.path.exists') as mock_exists:
            mock_exists.return_value = True
            
            with patch('src.backend.project_validator.Path.read_text') as mock_read_text:
                def read_text_side_effect(path):
                    if str(path).endswith("conda-project.yml"):
                        return sample_conda_project_yml
                    elif str(path).endswith("environment.yml"):
                        return sample_environment_yml
                    return ""
                
                mock_read_text.side_effect = read_text_side_effect
                
                result = validate_git_repository("https://github.com/test/repo.git")
        
        assert result["valid"] is True
        assert result["project_name"] == "test-project"
        assert result["temp_directory"] is not None
        mock_repo.clone_from.assert_called_once()
    
    @patch('src.backend.project_validator.git.Repo')
    def test_validate_git_repository_clone_failure(self, mock_repo_class):
        """Test git repository validation with clone failure."""
        mock_repo_class.clone_from.side_effect = Exception("Clone failed")
        
        result = validate_git_repository("https://github.com/test/repo.git")
        
        assert result["valid"] is False
        assert "Failed to clone repository" in result["errors"][0]
    
    @patch('src.backend.project_validator.git.Repo')
    def test_validate_git_repository_invalid_project(self, mock_repo_class, temp_dir):
        """Test git repository validation with invalid project."""
        # Mock git repository
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.clone_from.return_value = mock_repo
        
        # Mock cloned repository without conda-project.yml
        with patch('src.backend.project_validator.os.path.exists') as mock_exists:
            mock_exists.return_value = False
            
            result = validate_git_repository("https://github.com/test/repo.git")
        
        assert result["valid"] is False
        assert "conda-project.yml not found" in result["errors"][0]
    
    def test_cleanup_temp_directory_success(self, temp_dir):
        """Test successful temp directory cleanup."""
        # Create a temp directory
        temp_path = Path(temp_dir) / "test-temp"
        temp_path.mkdir()
        (temp_path / "test-file.txt").write_text("test content")
        
        # Verify directory exists
        assert temp_path.exists()
        
        # Clean up
        result = cleanup_temp_directory(str(temp_path))
        
        assert result["success"] is True
        assert not temp_path.exists()
    
    def test_cleanup_temp_directory_not_exists(self):
        """Test cleanup of non-existent directory."""
        result = cleanup_temp_directory("/non/existent/path")
        
        assert result["success"] is True
        assert "Directory does not exist" in result["message"]
    
    def test_cleanup_temp_directory_permission_error(self, temp_dir):
        """Test cleanup with permission error."""
        temp_path = Path(temp_dir) / "test-temp"
        temp_path.mkdir()
        
        # Mock permission error
        with patch('shutil.rmtree', side_effect=PermissionError("Permission denied")):
            result = cleanup_temp_directory(str(temp_path))
        
        assert result["success"] is False
        assert "Permission denied" in result["error"]
    
    def test_validate_conda_project_with_warnings(self, temp_dir):
        """Test validation with warnings."""
        # Create conda-project.yml with warnings
        conda_project_yml = Path(temp_dir) / "conda-project.yml"
        conda_project_yml.write_text("""name: test-project
environments:
  default:
    - environment.yml
variables: {}
commands:
  run:
    cmd: python main.py
    environment: default
""")
        
        # Create environment.yml with warnings
        environment_yml = Path(temp_dir) / "environment.yml"
        environment_yml.write_text("""name: default
channels:
  - conda-forge
dependencies:
  - python=3.11
variables: {}
# Missing platforms - this should generate a warning
""")
        
        result = validate_conda_project(temp_dir)
        
        assert result["valid"] is True
        assert len(result["warnings"]) > 0
        assert any("platforms" in warning.lower() for warning in result["warnings"])
    
    def test_validate_conda_project_relative_path(self, test_project_dir):
        """Test validation with relative path."""
        # Change to parent directory and use relative path
        parent_dir = Path(test_project_dir).parent
        relative_path = Path(test_project_dir).name
        
        result = validate_conda_project(relative_path)
        
        assert result["valid"] is True
        assert result["project_name"] == "test-project"
