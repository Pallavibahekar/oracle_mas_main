"""Main FastAPI application entry point."""

import json
import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.agents.data_sources_agent import (
    DataSourcesAgentExecutor,
    get_data_sources_agent_card,
)
from app.agents.internet_search_agent import (
    InternetSearchAgentExecutor,
    get_internet_search_agent_card,
)
from app.agents.router_agent import (
    RouterAgentExecutor,
    get_router_agent_card,
)
from app.services.tools_service import ToolsService
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.apps import A2AFastAPIApplication
from dotenv import load_dotenv

load_dotenv()

from app.controllers import health_router, datasources_agent_router
from app.core.config import settings


# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Manage application lifecycle events.

    Args:
        app: FastAPI application instance
    """
    try:
        # Startup
        logger.info(f"Starting {settings.app_name} v{settings.app_version}")
        logger.info(f"Environment: {settings.environment}")
        logger.info(f"Debug mode: {settings.debug}")

        # Connect to MCP servers using ToolsService
        tools_service = ToolsService()

        # Connect to MCP servers
        await tools_service.connect_to_mcp_servers()

        yield

    finally:
        # Shutdown - Clean up MCP server resources
        logger.info("Shutting down application...")

        # Disconnect from MCP servers
        tools_service = ToolsService()
        await tools_service.disconnect_from_mcp_servers()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)


# Add custom exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: The request that caused the exception
        exc: The exception that was raised

    Returns:
        JSONResponse: Error response
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": str(exc) if settings.debug else "An unexpected error occurred",
        },
    )


# Include routers
app.include_router(health_router, prefix="")

# Data Sources Agent
data_sources_agent_card = get_data_sources_agent_card()
data_sources_agent_executor = DataSourcesAgentExecutor()
data_sources_request_handler = DefaultRequestHandler(
    agent_executor=data_sources_agent_executor,
    task_store=InMemoryTaskStore(),
)
A2AFastAPIApplication(
    agent_card=data_sources_agent_card, http_handler=data_sources_request_handler
).add_routes_to_app(
    app,
    agent_card_url="/datasources-agent/.well-known/a2a",
    rpc_url="/datasources-agent",
)

# Internet Search Agent
internet_search_agent_card = get_internet_search_agent_card()
internet_search_agent_executor = InternetSearchAgentExecutor()
internet_search_request_handler = DefaultRequestHandler(
    agent_executor=internet_search_agent_executor,
    task_store=InMemoryTaskStore(),
)
A2AFastAPIApplication(
    agent_card=internet_search_agent_card, http_handler=internet_search_request_handler
).add_routes_to_app(
    app,
    agent_card_url="/internet-search-agent/.well-known/a2a",
    rpc_url="/internet-search-agent",
)

# Router Agent
router_agent_card = get_router_agent_card()
router_agent_executor = RouterAgentExecutor()
router_request_handler = DefaultRequestHandler(
    agent_executor=router_agent_executor,
    task_store=InMemoryTaskStore(),
)
A2AFastAPIApplication(
    agent_card=router_agent_card, http_handler=router_request_handler
).add_routes_to_app(
    app,
    agent_card_url="/router-agent/.well-known/a2a",
    rpc_url="/router-agent",
)

if __name__ == "__main__":
    import uvicorn

    print("Routes:")
    for route in app.routes:
        print(f"{route.name}: {route.path}")
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info" if not settings.debug else "debug",
    )
