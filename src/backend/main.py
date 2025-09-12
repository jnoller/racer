"""
Racer Backend API Server

A FastAPI-based orchestration server for deploying conda-project applications
to Docker containers with a Heroku/Fly.io-like REST API.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import os
from datetime import datetime

# Create FastAPI application
app = FastAPI(
    title="Racer API",
    description="Rapid deployment system for conda-projects",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Response models
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    service: str

class LivenessResponse(BaseModel):
    alive: bool
    timestamp: str
    uptime: str

# Global variables for tracking
start_time = datetime.now()

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Racer API Server",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
        "liveness": "/liveness"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring service health.
    
    Returns:
        HealthResponse: Service health status and metadata
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0",
        service="racer-api"
    )

@app.get("/liveness", response_model=LivenessResponse)
async def liveness_check():
    """
    Liveness probe endpoint for container orchestration.
    
    This endpoint is used by container orchestrators (like Kubernetes)
    to determine if the service is alive and should continue running.
    
    Returns:
        LivenessResponse: Service liveness status and uptime
    """
    uptime = datetime.now() - start_time
    return LivenessResponse(
        alive=True,
        timestamp=datetime.now().isoformat(),
        uptime=str(uptime)
    )

@app.get("/ready")
async def readiness_check():
    """
    Readiness probe endpoint for container orchestration.
    
    This endpoint indicates if the service is ready to accept traffic.
    In a full implementation, this would check database connections,
    external dependencies, etc.
    
    Returns:
        dict: Readiness status
    """
    # For now, always ready. In production, check dependencies here.
    return {
        "ready": True,
        "timestamp": datetime.now().isoformat(),
        "checks": {
            "database": "ok",  # Placeholder
            "docker": "ok",    # Placeholder
            "conda": "ok"      # Placeholder
        }
    }

if __name__ == "__main__":
    # Get configuration from environment variables
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )
