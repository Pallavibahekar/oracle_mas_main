import asyncio
import logging
import os
import signal
import subprocess
import sys
from threading import Lock
from typing import Any, List, Optional

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from app.core.config import settings


logger = logging.getLogger(__name__)


class ToolServiceMeta(type):
    """Meta class for ToolsService."""
    _instances = {}
    _lock: Lock = Lock()

    def __call__(cls, *args: Any, **kwds: Any) -> Any:
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwds)
        return cls._instances[cls]


class ToolsService(metaclass=ToolServiceMeta):
    _tools: List[BaseTool] = []
    _local_mcp_servers: List[subprocess.Popen] = []
    _mcp_client: Optional[MultiServerMCPClient] = None
    
    async def connect_to_mcp_servers(self):
        """
        Connect to MCP servers and initialize tools.
        """
        try:
            # Start local MCP server subprocess (RAG tool)
            rag_tool_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                "agents", "tools", "mcp", "rag_tool.py"
            )
            logger.info(f"Starting RAG MCP server from {rag_tool_path}")

            rag_process = subprocess.Popen(
                [sys.executable, rag_tool_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self._local_mcp_servers.append(rag_process)

            # Use provided config or default
            config = {
                "rag-tool": {
                    "transport": "streamable_http",
                    "url": settings.rag_tool_mcp_url,
                },
                "tavily": {
                    "transport": "streamable_http",
                    "url": settings.tavily_mcp_url,
                },
            }

            # Create MCP client
            self._mcp_client = MultiServerMCPClient(config)

            # Try to connect to MCP servers with retries
            max_attempts = 5
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.info(
                        f"Attempting to connect to MCP servers (attempt {attempt}/{max_attempts})..."
                    )

                    # Try to get tools - this will fail if servers aren't ready
                    tools = await self._mcp_client.get_tools()

                    logger.info(
                        f"Successfully connected to MCP servers! Found {len(tools)} tools"
                    )
                    for tool in tools:
                        logger.info(
                            " ".join(
                                f"""Tool {tool.name}:
                        Tool description: {tool.description}
                        Tool input schema: {tool.get_input_jsonschema()}
                        Tool output schema: {tool.get_output_jsonschema()}
                        """.split()
                            )
                        )
                    
                    # Add tools to the service
                    self.add_tools(tools)
                    break

                except Exception as e:
                    logger.warning(
                        f"Failed to connect to MCP servers on attempt {attempt}: {e}"
                    )

                    if attempt == max_attempts:
                        logger.error(
                            f"Failed to connect to MCP servers after {max_attempts} attempts."
                        )
                        raise Exception(
                            f"Failed to connect to MCP servers after {max_attempts} attempts"
                        )

                    # Wait before retrying with exponential backoff
                    await asyncio.sleep(2 * attempt)

        except Exception as e:
            logger.error(f"Error during MCP server connection: {e}")
            # Clean up if connection fails
            await self.disconnect_from_mcp_servers()
            raise

    async def disconnect_from_mcp_servers(self):
        """Disconnect from MCP servers and clean up resources."""
        logger.info("Disconnecting from MCP servers...")

        # Stop all local MCP server processes
        for process in self._local_mcp_servers:
            if process and process.poll() is None:  # Check if process is still running
                logger.info("Stopping MCP server process...")
                try:
                    process.send_signal(signal.SIGTERM)
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning(
                        "Process didn't terminate gracefully, forcing kill..."
                    )
                    process.kill()
                    process.wait()
                except Exception as e:
                    logger.error(f"Error stopping process: {e}")

        self._local_mcp_servers.clear()
        self._mcp_client = None
        logger.info("All MCP servers stopped")

    def add_tools(self, tools: List[BaseTool]):
        self._tools.extend(tools)
    
    def get_tools(self) -> List[BaseTool]:
        return self._tools
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        for tool in self._tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tools_by_names(self, names: List[str]) -> List[BaseTool]:
        return [tool for tool in self._tools if tool.name in names]