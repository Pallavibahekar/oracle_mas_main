"""Health check service implementation."""

import asyncio
from datetime import datetime
from typing import Dict, Any

from app.core.config import settings
from app.models.health_model import HealthResponse


class HealthService:
    """Service class for health check operations."""
    
    @staticmethod
    async def get_health_status() -> HealthResponse:
        """
        Get the current health status of the application.
        
        Returns:
            HealthResponse: Current health status with metadata
        """
        # Simulate some async health checks
        checks = await HealthService._perform_health_checks()
        
        # Determine overall status based on checks
        status = "healthy" if all(checks.values()) else "degraded"
        message = HealthService._generate_health_message(checks)
        
        return HealthResponse(
            status=status,
            message=message,
            timestamp=datetime.utcnow(),
            version=settings.app_version,
            environment=settings.environment
        )
    
    @staticmethod
    async def _perform_health_checks() -> Dict[str, bool]:
        """
        Perform various health checks on the system.
        
        Returns:
            Dict[str, bool]: Dictionary of health check results
        """
        checks = {}
        
        # Check application is running
        checks["app"] = True
        
        # Simulate database check (if configured)
        if settings.database_url:
            checks["database"] = await HealthService._check_database()
        
        # Simulate redis check (if configured)
        if settings.redis_url:
            checks["redis"] = await HealthService._check_redis()
        
        # Add more health checks as needed
        # For example: external API connectivity, disk space, memory usage, etc.
        
        return checks
    
    @staticmethod
    async def _check_database() -> bool:
        """
        Check database connectivity.
        
        Returns:
            bool: True if database is accessible, False otherwise
        """
        # Simulate database check with a small delay
        await asyncio.sleep(0.1)
        # In a real implementation, you would actually check the database connection
        return True
    
    @staticmethod
    async def _check_redis() -> bool:
        """
        Check Redis connectivity.
        
        Returns:
            bool: True if Redis is accessible, False otherwise
        """
        # Simulate Redis check with a small delay
        await asyncio.sleep(0.1)
        # In a real implementation, you would actually check the Redis connection
        return True
    
    @staticmethod
    def _generate_health_message(checks: Dict[str, bool]) -> str:
        """
        Generate a descriptive health message based on check results.
        
        Args:
            checks: Dictionary of health check results
            
        Returns:
            str: Descriptive health message
        """
        if all(checks.values()):
            return "All systems operational"
        
        failed_checks = [name for name, status in checks.items() if not status]
        if failed_checks:
            return f"Service degraded: {', '.join(failed_checks)} check(s) failed"
        
        return "Service is running"
    
    @staticmethod
    async def get_simple_health() -> Dict[str, Any]:
        """
        Get a simple health check response.
        
        Returns:
            Dict[str, Any]: Simple health status
        """
        return {
            "status": "ok",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.app_version
        }
