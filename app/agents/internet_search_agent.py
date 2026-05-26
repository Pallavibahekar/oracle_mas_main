
"""Manual ReAct Agent Graph with Internet Search tool."""

import os
from typing import TypedDict, Annotated
import uuid
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import new_agent_text_message, new_task, new_text_artifact
from langgraph.graph import StateGraph, END, add_messages
from langgraph.graph.state import RunnableConfig
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from app.core.config import settings
from app.services.tools_service import ToolsService
import logging

checkpointer = InMemorySaver()

SYSTEM_PROMPT = """You are an intelligent internet search assistant specialized in finding and synthesizing information from web sources.

## CRITICAL SEARCH WORKFLOW - Follow this sequence:

1. **FIRST SEARCH**: When you receive a user query, use the tavily_search tool to find relevant information
2. **ANALYZE RESULTS**: After receiving search results, carefully analyze them to determine if they answer the user's question
3. **DECISION POINT**: 
   - If results contain sufficient information → PROVIDE THE ANSWER (do NOT search again)
   - If results are incomplete or need clarification → SEARCH AGAIN with refined terms (maximum 2 additional searches)
   - If no relevant results after 3 total searches → Summarize what you found and provide the best possible answer

## IMPORTANT: Search Limits

- **MAXIMUM 3 SEARCHES** per user query - no exceptions
- **DO NOT** continuously search for "perfect" information - work with what you find
- **DO NOT** search again just to verify - trust your results
- **ALWAYS** provide a concrete answer after analyzing search results
- **SUMMARIZE** findings after reaching the search limit

## Your Capabilities:
- Access to Tavily Search API for real-time web searching
- Ability to search for current events, facts, research, and general information
- Skills in analyzing and summarizing search results

## Your Approach:
1. **Strategic Searching**: Use specific, relevant keywords
2. **Efficient Analysis**: Extract key information from each search
3. **Quick Synthesis**: Combine findings into a coherent answer
4. **Clear Communication**: Provide direct, factual answers

## Best Practices:
- Make your first search count - use the most relevant query
- Analyze results thoroughly before deciding to search again
- If you hit the 3-search limit, synthesize what you have
- Always provide a conclusive answer, even if information is limited

## Response Format:
- Lead with a direct answer to the user's question
- Provide supporting details from your searches
- Include source citations when available
- If information is limited, clearly state what you found
- Do NOT suggest additional searches after reaching the limit

Remember: Your goal is to efficiently find information and provide concrete answers within the search limit, not to search endlessly for perfect information."""

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    search_count: int = 0
    max_searches: int = 3


def should_continue(state: AgentState):
    """Route to tools or end based on search count and tool calls."""
    last_message = state["messages"][-1]
    
    # Check if we've reached the maximum number of searches
    if state.get("search_count", 0) >= state.get("max_searches", 3):
        logger.info(f"Reached maximum search limit ({state.get('max_searches', 3)}), ending conversation")
        return END
    
    # Check if the agent wants to use tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    
    return END


def create_internet_search_agent_graph():
    """Create manual ReAct agent graph."""
    from app.agents.llm_models import data_sources_agent_llm

    async def dynamic_tools_node(state: AgentState):
        """Dynamic tools node with search counting."""
        tools = ToolsService().get_tools_by_names(["tavily_search"])
        tool_node = ToolNode(tools)
        
        # Check if this is a tavily_search call and increment counter
        last_message = state["messages"][-1]
        search_count = state.get("search_count", 0)
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                # Access the tool name correctly based on the tool_call structure
                tool_name = getattr(tool_call, "name", None) or (tool_call.get("name") if isinstance(tool_call, dict) else None)
                if tool_name == "tavily_search":
                    search_count += 1
                    logger.info(f"Executing search #{search_count}")
                    break
        
        # Execute the tools
        result = await tool_node.ainvoke(state)
        
        # Return updated state with search count
        return {"messages": result["messages"], "search_count": search_count}

    async def agent_node(state: AgentState):
        """Agent reasoning node."""
        tools = ToolsService().get_tools_by_names(["tavily_search"])
        bound_model = data_sources_agent_llm.bind_tools(tools)
        
        search_count = state.get("search_count", 0)
        max_searches = state.get("max_searches", 3)
        
        # Add search count context to help the agent track its searches
        search_context = f"\n\nIMPORTANT: You have performed {search_count} out of {max_searches} maximum allowed searches."
        if search_count >= max_searches - 1:
            search_context += " This is your LAST allowed search. After this, you MUST provide a final conclusive answer based on all the information you've gathered."
        elif search_count > 0:
            search_context += f" You have {max_searches - search_count} searches remaining."
        
        logger.info(f"Agent reasoning - Search count: {search_count}/{max_searches}")

        response = await bound_model.ainvoke(
            [SystemMessage(content=SYSTEM_PROMPT + search_context)] + state["messages"]
        )
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", dynamic_tools_node)

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer)


def get_internet_search_agent_card():
    return AgentCard(
        name="Internet Search Agent",
        description="""An agent that can search the internet for information. 
        Requests to this agent will always result in a Task being created""",
        url=f"http://{settings.host}:{settings.port}/internet-search-agent",
        capabilities=AgentCapabilities(),
        skills=[
            AgentSkill(
                id="search-internet",
                description="Search the internet for information.",
                name="Search internet",
                tags=["search-internet"],
            ),
        ],
        default_input_modes=["text"],
        default_output_modes=["text"],
        version="1.0.0",
    )


class InternetSearchAgentExecutor(AgentExecutor):
    def __init__(self):
        super().__init__()
        self._agent = None

    @property
    def agent(self):
        """Lazy initialization of agent graph to ensure tools are available."""
        if self._agent is None:
            self._agent = create_internet_search_agent_graph()
        return self._agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task
        message = context.message
        if not task:
            task = new_task(message)
            await event_queue.enqueue_event(task)
        
        # Initialize state with search tracking
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "search_count": 0,
            "max_searches": 3
        }
        
        result = await self.agent.ainvoke(
            initial_state,
            config=RunnableConfig(configurable={"thread_id": task.context_id}),
        )
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                append=False,
                context_id=task.context_id,
                task_id=task.id,
                last_chunk=True,
                artifact=new_text_artifact(
                    name="response",
                    description="Response from internet search agent.",
                    text=result["messages"][-1].content,
                ),
            )
        )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(state=TaskState.completed),
                # Adding this for history purposes
                message=new_agent_text_message(
                    text=result["messages"][-1].content,
                    task_id=task.id,
                    context_id=task.context_id,
                ),
                final=True,
                context_id=task.context_id,
                task_id=task.id,
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")