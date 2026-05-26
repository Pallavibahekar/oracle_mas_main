"""DelegateToAgent tool for routing requests to specialized agents."""

from typing import Annotated, Dict, Any, Optional
import uuid
from a2a.client import A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
    SendMessageSuccessResponse,
    Task,
    TaskStatus,
    TaskState,
)
import httpx
from langchain_core.messages import ToolMessage
from langchain.tools import tool
from langchain.tools import ToolRuntime, InjectedToolArg
from langgraph.types import Command
import logging
from app.agents.data_sources_agent import get_data_sources_agent_card
from app.agents.internet_search_agent import get_internet_search_agent_card

logger = logging.getLogger(__name__)


@tool
async def delegate_to_agent(
    agent_name: str,
    query: str,
    runtime: Annotated[ToolRuntime, InjectedToolArg],
    *args, **kwargs
) -> Command:
    """Delegate a query to a specialized agent.
    
    Use this to route requests to either the Data Sources Agent 
    (for RAG queries, document search, vector database operations) 
    or the Internet Search Agent (for web searches, current events, real-time information).
    
    Args:
        agent_name: Name of the agent to delegate to. Options: 'data_sources_agent', 'internet_search_agent'
        query: The query or request to pass to the specialized agent
        runtime: Runtime context provided by LangGraph framework (injected automatically)
    
    Returns:
        Command: Update command for the state with the response from the delegated agent
    """
    agent_card = None
    if agent_name == "data_sources_agent":
        agent_card = get_data_sources_agent_card()
    elif agent_name == "internet_search_agent":
        agent_card = get_internet_search_agent_card()
    else:
        raise ValueError(f"Invalid agent name: {agent_name}")
        
    update = {}
    from app.agents.router_agent import AgentState
    
    state: AgentState = runtime.state
    if state["current_agent"] != agent_name:
        update["current_agent"] = agent_name
        update["task_id"] = None

    message_id = str(uuid.uuid4())
    payload = {
        "message": {
            "role": "user",
            "parts": [{"type": "text", "text": query}],
            "messageId": message_id,
        }
    }
    req = SendMessageRequest(
        id=message_id, params=MessageSendParams.model_validate(payload)
    )
    httpx_client = httpx.AsyncClient(timeout=300)
    a2a_client = A2AClient(httpx_client, agent_card, url=agent_card.url)
    tool_message = None
    
    try:
        res: SendMessageResponse = await a2a_client.send_message(req)
        logger.info(
            f"res from delegate tool: \n {res.model_dump_json(exclude_none=True, indent=2)}",
        )

        if not isinstance(res.root, SendMessageSuccessResponse):
            logger.error("received non-success response. Aborting get task ")
            raise ValueError("received non-success response. Aborting get task ")

        if not isinstance(res.root.result, Task):
            logger.error("received non-task response. Aborting get task ")
            raise ValueError("received non-task response. Aborting get task ")

        task = res.root.result
        update["task_id"] = task.id
        tool_message = None
        
        if task.status.state == TaskState.completed:
            # Assuming the first artifact is the response and only has text part
            tool_message = ToolMessage(
                content=task.artifacts[0].model_dump_json(indent=2, exclude_none=True), 
                tool_call_id=runtime.tool_call_id
            )
            # Updating the task id to None as request has been completed
            update["task_id"] = None
        else:
            # Assuming the last message is the response
            tool_message = ToolMessage(
                content=task.history[-1].model_dump_json(indent=2, exclude_none=True), 
                tool_call_id=runtime.tool_call_id
            )
        update["messages"] = [tool_message]
        
    except Exception as e:
        tool_message = ToolMessage(
            content=f"Error in delegating to {agent_name}: {e}",
            tool_call_id=runtime.tool_call_id
        )
        update["messages"] = [tool_message]
        
    return Command(update=update)


# Keep the old class for backwards compatibility, but it won't be used
class DelegateToAgent:
    """Legacy class - use delegate_to_agent function instead."""
    pass