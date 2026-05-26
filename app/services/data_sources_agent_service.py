"""Minimal service for data sources agent."""

from langchain_core.messages import HumanMessage
from app.agents.data_sources_agent import data_sources_agent


class DataSourcesAgentService:
    """Minimal service for data sources agent."""
    
    def __init__(self):
        self.agent = data_sources_agent
    
    def invoke(self, query: str):
        """Minimal invoke."""
        return self.agent.invoke({"messages": [HumanMessage(content=query)]})
    
    async def ainvoke(self, query: str):
        """Minimal async invoke."""
        return await self.agent.ainvoke({"messages": [HumanMessage(content=query)]})


# Create instance
data_sources_agent_service = DataSourcesAgentService()