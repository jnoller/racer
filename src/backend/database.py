"""
Database manager for the Racer backend.
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

try:
    from models import Base, Project, Container, ScaleGroup
except ImportError:
    from .models import Base, Project, Container, ScaleGroup


class DatabaseManager:
    """Manages database operations for the Racer backend."""

    def __init__(self, database_url: str = None):
        """Initialize the database manager."""
        if database_url is None:
            # Default to SQLite database in the backend directory
            db_path = os.path.join(os.path.dirname(__file__), "racer.db")
            database_url = f"sqlite:///{db_path}"

        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False}
            if "sqlite" in database_url
            else {},
        )
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def init_database(self) -> bool:
        """Initialize the database by creating all tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            return True
        except SQLAlchemyError as e:
            print(f"Failed to initialize database: {e}")
            return False

    def cleanup_database(self) -> bool:
        """Clean up the database by dropping all tables."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            return True
        except SQLAlchemyError as e:
            print(f"Failed to cleanup database: {e}")
            return False

    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """Close a database session."""
        session.close()

    # Project operations
    def create_project(
        self,
        name: str,
        project_path: str = None,
        git_url: str = None,
        image_name: str = None,
        app_port: int = None,
    ) -> Optional[Project]:
        """Create a new project."""
        session = self.get_session()
        try:
            project = Project(
                name=name,
                project_path=project_path,
                git_url=git_url,
                image_name=image_name or f"{name}:latest",
                app_port=app_port or 8000,
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to create project: {e}")
            return None
        finally:
            self.close_session(session)

    def get_project(
        self, project_id: int = None, name: str = None
    ) -> Optional[Project]:
        """Get a project by ID or name."""
        session = self.get_session()
        try:
            if project_id:
                return session.query(Project).filter(Project.id == project_id).first()
            elif name:
                return session.query(Project).filter(Project.name == name).first()
            return None
        except SQLAlchemyError as e:
            print(f"Failed to get project: {e}")
            return None
        finally:
            self.close_session(session)

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get a project by name (convenience method)."""
        return self.get_project(name=name)

    def list_projects(self) -> List[Project]:
        """List all projects."""
        session = self.get_session()
        try:
            return session.query(Project).all()
        except SQLAlchemyError as e:
            print(f"Failed to list projects: {e}")
            return []
        finally:
            self.close_session(session)

    def delete_project(self, project_id: int) -> bool:
        """Delete a project and all its containers."""
        session = self.get_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to delete project: {e}")
            return False
        finally:
            self.close_session(session)

    # Container operations
    def create_container(
        self,
        container_id: str,
        container_name: str,
        project_id: int,
        status: str = "running",
        ports: Dict[str, Any] = None,
        environment: Dict[str, Any] = None,
        command: str = None,
        scale_group_id: int = None,
    ) -> Optional[Container]:
        """Create a new container record."""
        session = self.get_session()
        try:
            container = Container(
                container_id=container_id,
                container_name=container_name,
                project_id=project_id,
                status=status,
                ports=ports,
                environment=environment,
                command=command,
                scale_group_id=scale_group_id,
            )
            session.add(container)
            session.commit()
            session.refresh(container)
            return container
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to create container: {e}")
            return None
        finally:
            self.close_session(session)

    def get_container(
        self, container_id: str = None, container_name: str = None
    ) -> Optional[Container]:
        """Get a container by ID or name."""
        session = self.get_session()
        try:
            if container_id:
                return (
                    session.query(Container)
                    .filter(Container.container_id == container_id)
                    .first()
                )
            elif container_name:
                return (
                    session.query(Container)
                    .filter(Container.container_name == container_name)
                    .first()
                )
            return None
        except SQLAlchemyError as e:
            print(f"Failed to get container: {e}")
            return None
        finally:
            self.close_session(session)

    def list_containers(
        self, project_id: int = None, status: str = None
    ) -> List[Container]:
        """List containers, optionally filtered by project or status."""
        session = self.get_session()
        try:
            query = session.query(Container)
            if project_id:
                query = query.filter(Container.project_id == project_id)
            if status:
                query = query.filter(Container.status == status)
            return query.all()
        except SQLAlchemyError as e:
            print(f"Failed to list containers: {e}")
            return []
        finally:
            self.close_session(session)

    def update_container_status(self, container_id: str, status: str) -> bool:
        """Update container status."""
        session = self.get_session()
        try:
            container = (
                session.query(Container)
                .filter(Container.container_id == container_id)
                .first()
            )
            if container:
                container.status = status
                if status == "stopped":
                    container.stopped_at = datetime.utcnow()
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to update container status: {e}")
            return False
        finally:
            self.close_session(session)

    def delete_container(self, container_id: str) -> bool:
        """Delete a container record."""
        session = self.get_session()
        try:
            container = (
                session.query(Container)
                .filter(Container.container_id == container_id)
                .first()
            )
            if container:
                session.delete(container)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to delete container: {e}")
            return False
        finally:
            self.close_session(session)

    # Scale group operations
    def create_scale_group(
        self,
        name: str,
        service_id: str = None,
        replicas: int = 1,
        image: str = None,
        ports: dict = None,
        environment: dict = None,
    ) -> Optional[ScaleGroup]:
        """Create a new scale group."""
        session = self.get_session()
        try:
            scale_group = ScaleGroup(
                name=name,
                service_id=service_id,
                replicas=replicas,
                image=image or "",
                ports=ports or {},
                environment=environment or {},
            )
            session.add(scale_group)
            session.commit()
            session.refresh(scale_group)
            return scale_group
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to create scale group: {e}")
            return None
        finally:
            self.close_session(session)

    def get_scale_group(self, name: str) -> Optional[ScaleGroup]:
        """Get a scale group by name."""
        session = self.get_session()
        try:
            return session.query(ScaleGroup).filter(ScaleGroup.name == name).first()
        except SQLAlchemyError as e:
            print(f"Failed to get scale group: {e}")
            return None
        finally:
            self.close_session(session)

    def get_scale_group_by_name(self, name: str) -> Optional[ScaleGroup]:
        """Get a scale group by name (alias for get_scale_group)."""
        return self.get_scale_group(name)

    def get_scale_group_by_service_id(self, service_id: str) -> Optional[ScaleGroup]:
        """Get a scale group by service ID."""
        session = self.get_session()
        try:
            return (
                session.query(ScaleGroup)
                .filter(ScaleGroup.service_id == service_id)
                .first()
            )
        except SQLAlchemyError as e:
            print(f"Failed to get scale group by service ID: {e}")
            return None
        finally:
            self.close_session(session)

    def update_scale_group(self, scale_group_id: int, **kwargs) -> bool:
        """Update a scale group."""
        session = self.get_session()
        try:
            scale_group = (
                session.query(ScaleGroup)
                .filter(ScaleGroup.id == scale_group_id)
                .first()
            )
            if scale_group:
                for key, value in kwargs.items():
                    if hasattr(scale_group, key):
                        setattr(scale_group, key, value)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to update scale group: {e}")
            return False
        finally:
            self.close_session(session)

    def delete_scale_group(self, scale_group_id: int) -> bool:
        """Delete a scale group by ID."""
        session = self.get_session()
        try:
            scale_group = (
                session.query(ScaleGroup)
                .filter(ScaleGroup.id == scale_group_id)
                .first()
            )
            if scale_group:
                session.delete(scale_group)
                session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to delete scale group: {e}")
            return False
        finally:
            self.close_session(session)

    # Utility methods
    def get_running_containers(self) -> List[Container]:
        """Get all running containers."""
        return self.list_containers(status="running")

    def get_project_containers(self, project_name: str) -> List[Container]:
        """Get all containers for a project by name."""
        session = self.get_session()
        try:
            project = (
                session.query(Project).filter(Project.name == project_name).first()
            )
            if project:
                return (
                    session.query(Container)
                    .filter(Container.project_id == project.id)
                    .all()
                )
            return []
        except SQLAlchemyError as e:
            print(f"Failed to get project containers: {e}")
            return []
        finally:
            self.close_session(session)

    def cleanup_stopped_containers(self) -> int:
        """Remove records for stopped containers."""
        session = self.get_session()
        try:
            stopped_containers = (
                session.query(Container).filter(Container.status == "stopped").all()
            )
            count = len(stopped_containers)
            for container in stopped_containers:
                session.delete(container)
            session.commit()
            return count
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Failed to cleanup stopped containers: {e}")
            return 0
        finally:
            self.close_session(session)
