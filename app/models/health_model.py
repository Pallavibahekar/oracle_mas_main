"""Health check response models."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Response model for health check endpoints."""
    
    status: str = Field(
        ...,
        description="Health status of the service",
        example="healthy"
    )
    message: str = Field(
        ...,
        description="Descriptive message about the service status",
        example="Service is running normally"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the health check"
    )
    version: str = Field(
        ...,
        description="Application version",
        example="0.1.0"
    )
    environment: Optional[str] = Field(
        None,
        description="Current environment",
        example="development"
    )
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "Service is running normally",
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "0.1.0",
                "environment": "development"
            }
        }
