"""Health check controller with API routes."""

from typing import Dict, Any

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.models.health_model import HealthResponse
from app.services.health_service import HealthService

# Create router instance
router = APIRouter(
    tags=["Health"],
    responses={
        status.HTTP_503_SERVICE_UNAVAILABLE: {
            "description": "Service is unhealthy",
            "content": {
                "application/json": {
                    "example": {"status": "unhealthy", "message": "Service unavailable"}
                }
            }
        }
    }
)

# Initialize service
health_service = HealthService()


@router.get(
    "/",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Root endpoint",
    description="Welcome message for the API"
)
async def root() -> Dict[str, str]:
    """
    Root endpoint that returns a welcome message.
    
    Returns:
        Dict[str, str]: Welcome message with API information
    """
    return {
        "message": "Welcome to Oracle MAS API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check the health status of the service and its dependencies",
    responses={
        status.HTTP_200_OK: {
            "description": "Service is healthy",
            "model": HealthResponse
        }
    }
)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint.
    
    Performs various health checks on the service and its dependencies,
    returning detailed status information.
    
    Returns:
        HealthResponse: Detailed health status of the service
        
    Raises:
        HTTPException: If service is critically unhealthy
    """
    # Delegate to service layer
    health_status = await health_service.get_health_status()
    
    # If service is critically unhealthy, return 503
    if health_status.status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status.model_dump()
        )
    
    return health_status


@router.get(
    "/health/simple",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Simple health check",
    description="Quick health check that returns minimal status information"
)
async def simple_health() -> Dict[str, Any]:
    """
    Simple health check endpoint for monitoring tools.
    
    Returns a minimal response suitable for automated monitoring systems
    like Kubernetes liveness probes.
    
    Returns:
        Dict[str, Any]: Simple health status
    """
    return await health_service.get_simple_health()
