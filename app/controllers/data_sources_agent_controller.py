"""Datasources agent controller with API routes."""

from typing import Dict, Any

from fastapi import APIRouter, status
from pydantic import BaseModel

# Create router instance
router = APIRouter(
    prefix="/datasource-agent",
    tags=["Datasource Agent"],
)


# Simple request model
class DatasourceRequest(BaseModel):
    """Request model for datasource agent."""
    query: str
    datasource_id: str
    parameters: Dict[str, Any] = {}


# Simple response model
class DatasourceResponse(BaseModel):
    """Response model for datasource agent."""
    success: bool
    data: Dict[str, Any]
    message: str = "Operation completed successfully"


@router.post(
    "/invoke",
    response_model=DatasourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Invoke datasource agent",
    description="Process a request through the datasource agent"
)
async def invoke_datasource_agent(request: DatasourceRequest) -> DatasourceResponse:
    """
    Invoke the datasource agent with the provided parameters.
    
    Args:
        request: DatasourceRequest containing query and parameters
    
    Returns:
        DatasourceResponse: Result of the datasource agent operation
    """
    # Sample processing logic (replace with actual implementation)
    response_data = {
        "query_received": request.query,
        "datasource": request.datasource_id,
        "parameters_count": len(request.parameters),
        "result": "Sample response data"
    }
    
    return DatasourceResponse(
        success=True,
        data=response_data,
        message=f"Successfully processed query for datasource: {request.datasource_id}"
    )
