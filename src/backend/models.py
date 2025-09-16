"""
Database models for the Racer backend.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    Text,
    JSON,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Project(Base):
    """Model for tracking projects."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    project_path = Column(String(500), nullable=True)
    git_url = Column(String(500), nullable=True)
    image_name = Column(String(255), nullable=False)
    app_port = Column(Integer, nullable=True, default=8000)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    containers = relationship(
        "Container", back_populates="project", cascade="all, delete-orphan"
    )


class Container(Base):
    """Model for tracking containers."""

    __tablename__ = "containers"

    id = Column(Integer, primary_key=True, index=True)
    container_id = Column(String(64), nullable=False, unique=True, index=True)
    container_name = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="running")
    ports = Column(JSON, nullable=True)  # Store port mappings as JSON
    environment = Column(JSON, nullable=True)  # Store environment variables as JSON
    command = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="containers")


class ScaleGroup(Base):
    """Model for tracking scaled project groups (Docker Swarm deployments)."""

    __tablename__ = "scale_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Service/project name
    service_id = Column(
        String(64), nullable=True, unique=True, index=True
    )  # Swarm service ID
    replicas = Column(Integer, nullable=False, default=1)
    image = Column(String(255), nullable=False)
    ports = Column(JSON, nullable=True)  # Store port mappings as JSON
    environment = Column(JSON, nullable=True)  # Store environment variables as JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    containers = relationship("Container", back_populates="scale_group")


# Add scale_group relationship to Container
Container.scale_group_id = Column(
    Integer, ForeignKey("scale_groups.id"), nullable=True, index=True
)
Container.scale_group = relationship("ScaleGroup", back_populates="containers")
