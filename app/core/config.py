"""Application configuration management."""

from typing import Optional

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application settings
    app_name: str = "Oracle MAS API"
    app_version: str = "0.1.0"
    app_description: str = "FastAPI application with controller-service pattern"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8080
    reload: bool = True
    
    # CORS settings
    cors_origins: list[str] = ["*"]
    cors_credentials: bool = True
    cors_methods: list[str] = ["*"]
    cors_headers: list[str] = ["*"]
    
    # Bedrock settings
    data_sources_agent_model_id: str = "us.meta.llama4-scout-17b-instruct-v1:0"
    data_sources_agent_region_name: str = "us-east-2"
    aws_bearer_token_bedrock: str = "a_secret_value"


    # Neo4j settings
    neo4j_host: str = "localhost"
    neo4j_username: str = "neo4j"
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_password: str = ""
    neo4j_database: str = "neo4j"
    neo4j_http_port: int = 7474
    neo4j_bolt_port: int = 7687

    # Qdrant settings
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection_name: str = "my-collection"
    qdrant_using: str = "chunk_vector"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # MCP settings
    rag_tool_mcp_url: str = "http://localhost:8092/mcp"
    tavily_api_key: str = "your_tavily_api_key"
    
    @computed_field
    @property
    def tavily_mcp_url(self) -> str:
        """Dynamically compute the Tavily MCP URL with the current API key."""
        return f"https://mcp.tavily.com/mcp/?tavilyApiKey={self.tavily_api_key}"

# Create a singleton instance
settings = Settings()
