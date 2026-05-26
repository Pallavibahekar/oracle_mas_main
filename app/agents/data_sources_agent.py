"""Manual ReAct Agent Graph with RAG tool."""

import os
from pkgutil import get_data
from typing import TypedDict, Annotated
import uuid
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from langgraph.graph import StateGraph, END, add_messages
from langgraph.graph.state import RunnableConfig
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
import app.agents.tools.mcp.rag_tool as rag_tool
from langgraph.checkpoint.memory import InMemorySaver
from app.core.config import settings
from app.services.tools_service import ToolsService
import logging
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

checkpointer = InMemorySaver()

SYSTEM_PROMPT = """You are an intelligent Data Sources Assistant specialized in helping users search, retrieve, and analyze information from various data sources using RAG (Retrieval-Augmented Generation) capabilities.

## CRITICAL WORKFLOW - Follow this sequence:

1. **FIRST SEARCH**: When you receive a user query, use the query-vector-db tool to search for relevant information
2. **ANALYZE RESULTS**: After receiving search results, carefully analyze them to determine if they contain sufficient information to answer the user's question
3. **DECISION POINT**: 
   - If the results contain relevant information that answers the query → PROVIDE THE ANSWER (do NOT search again)
   - If the results are incomplete or don't fully address the query → SEARCH AGAIN with refined terms (maximum 2 additional searches)
   - If no relevant results after 3 total searches → Inform the user that no relevant information was found

## IMPORTANT: Avoid Looping

- **DO NOT** continuously search if you already have relevant information
- **DO NOT** search again just to "verify" or "double-check" - trust your initial results
- **ALWAYS** provide an answer after analyzing search results unless they are completely irrelevant
- **LIMIT** yourself to maximum 3 searches total for any single query

## Your Core Responsibilities

1. **Information Retrieval**: Search and retrieve relevant information from connected data sources
2. **Query Understanding**: Interpret user queries accurately and translate them into effective search strategies
3. **Result Analysis**: Thoroughly analyze retrieved documents to extract answers
4. **Source Attribution**: Always cite and reference the sources of information you provide
5. **Data Synthesis**: Combine information from multiple sources when needed

## How to Use Your Tools

You have access to:
- `query-vector-db`: Search through indexed documents using semantic similarity
- `ingest-document`: Add new documents to the vector database

## Response Guidelines

1. **Search First**: Always start with a search unless ingesting a document
2. **Analyze Thoroughly**: Extract all relevant information from search results
3. **Answer Decisively**: Once you have relevant information, provide a comprehensive answer
4. **Cite Sources**: Reference the documents/chunks where information was found
5. **Be Concise**: Avoid unnecessary additional searches if you have the answer

## Error Handling

- If a search fails technically, try once more with simpler terms
- If no results found, clearly state this and suggest alternative approaches
- Be transparent about limitations in the available data

Remember: Your goal is to efficiently retrieve information and provide answers, NOT to loop endlessly searching for perfect information."""

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


def create_data_sources_agent_graph():
    """Create manual ReAct agent graph."""
    from app.agents.llm_models import data_sources_agent_llm

    async def dynamic_tools_node(state: AgentState):
        """Dynamic tools node with search counting."""
        tools = ToolsService().get_tools_by_names(["query-vector-db", "ingest-document"])
        tool_node = ToolNode(tools)
        
        # Check if this is a query-vector-db call and increment counter
        last_message = state["messages"][-1]
        search_count = state.get("search_count", 0)
        
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                # Access the tool name correctly based on the tool_call structure
                tool_name = getattr(tool_call, "name", None) or (tool_call.get("name") if isinstance(tool_call, dict) else None)
                if tool_name == "query-vector-db":
                    search_count += 1
                    logger.info(f"Executing search #{search_count}")
                    break
        
        # Execute the tools
        result = await tool_node.ainvoke(state)
        
        # Return updated state with search count
        return {"messages": result["messages"], "search_count": search_count}
    
    async def agent_node(state: AgentState):
        """Agent reasoning node."""
        tools = ToolsService().get_tools_by_names(["query-vector-db", "ingest-document"])
        bound_model = data_sources_agent_llm.bind_tools(tools)
        
        search_count = state.get("search_count", 0)
        max_searches = state.get("max_searches", 3)
        
        # Add search count context to help the agent track its searches
        search_context = f"\n\nIMPORTANT: You have performed {search_count} out of {max_searches} maximum allowed searches."
        if search_count >= max_searches - 1:
            search_context += " This is your LAST allowed search. After this, you MUST provide a final answer."
        
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


def get_data_sources_agent_card():
    return AgentCard(
        name="Data Sources Agent",
        description="""An agent that can ingest and query data from vector database. 
        Requests to this agent will always result in a Task being created""",
        url=f"http://{settings.host}:{settings.port}/datasources-agent",
        capabilities=AgentCapabilities(),
        skills=[
            AgentSkill(
                id="ingest-document",
                description="Ingest a document into the vector database",
                name="Ingest document",
                tags=["ingest-document"],
            ),
            AgentSkill(
                id="query-vector-db",
                description="Query the vector database for a specific query to get relevant documents",
                name="Query vector database",
                tags=["query-vector-db"],
            ),
        ],
        default_input_modes=["text"],
        default_output_modes=["text"],
        version="1.0.0",
    )


class DataSourcesAgentExecutor(AgentExecutor):
    def __init__(self):
        super().__init__()
        self._agent = None

    @property
    def agent(self):
        """Lazy initialization of agent graph to ensure tools are available."""
        if self._agent is None:
            self._agent = create_data_sources_agent_graph()
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
                    description="Response from data sources agent.",
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
