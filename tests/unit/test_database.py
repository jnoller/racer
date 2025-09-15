"""
Unit tests for database functionality.
"""

import pytest
from tests.test_db_utils import TestDatabaseManager


class TestDatabase:
    """Test cases for database operations."""
    
    def test_database_init(self):
        """Test database initialization."""
        with TestDatabaseManager() as db:
            # Database should be initialized
            assert db is not None
    
    def test_project_crud(self):
        """Test project CRUD operations."""
        with TestDatabaseManager() as db:
            # Create project
            project = db.create_project(
                name="test-project",
                project_path="/tmp/test",
                image_name="test:latest"
            )
            assert project is not None
            assert project.name == "test-project"
            assert project.image_name == "test:latest"
            
            # Get project
            retrieved = db.get_project(name="test-project")
            assert retrieved is not None
            assert retrieved.id == project.id
            
            # List projects
            projects = db.list_projects()
            assert len(projects) == 1
            assert projects[0].name == "test-project"
            
            # Delete project
            success = db.delete_project(project.id)
            assert success is True
            
            # Verify deletion
            deleted = db.get_project(name="test-project")
            assert deleted is None
    
    def test_container_crud(self):
        """Test container CRUD operations."""
        with TestDatabaseManager() as db:
            # Create project first
            project = db.create_project(
                name="test-project",
                image_name="test:latest"
            )
            assert project is not None
            
            # Create container
            container = db.create_container(
                container_id="test-container-123",
                container_name="test-container",
                project_id=project.id,
                status="running",
                ports={"8000": 8000},
                environment={"DEBUG": "true"}
            )
            assert container is not None
            assert container.container_id == "test-container-123"
            assert container.status == "running"
            
            # Get container
            retrieved = db.get_container(container_id="test-container-123")
            assert retrieved is not None
            assert retrieved.container_name == "test-container"
            
            # Update status
            success = db.update_container_status("test-container-123", "stopped")
            assert success is True
            
            # Verify update
            updated = db.get_container(container_id="test-container-123")
            assert updated.status == "stopped"
            
            # List containers
            containers = db.list_containers(project_id=project.id)
            assert len(containers) == 1
            
            # Delete container
            success = db.delete_container("test-container-123")
            assert success is True
            
            # Verify deletion
            deleted = db.get_container(container_id="test-container-123")
            assert deleted is None
    
    def test_scale_group_crud(self):
        """Test scale group CRUD operations."""
        with TestDatabaseManager() as db:
            # Create scale group
            scale_group = db.create_scale_group(
                project_name="test-project",
                instances=3,
                use_load_balancer=False
            )
            assert scale_group is not None
            assert scale_group.project_name == "test-project"
            assert scale_group.instances == 3
            
            # Get scale group
            retrieved = db.get_scale_group("test-project")
            assert retrieved is not None
            assert retrieved.id == scale_group.id
            
            # Delete scale group
            success = db.delete_scale_group("test-project")
            assert success is True
            
            # Verify deletion
            deleted = db.get_scale_group("test-project")
            assert deleted is None
