"""LLM models."""

from langchain_aws import ChatBedrockConverse
from app.core.config import settings

data_sources_agent_llm = ChatBedrockConverse(
    model_id=settings.data_sources_agent_model_id,
    region_name=settings.data_sources_agent_region_name,
)