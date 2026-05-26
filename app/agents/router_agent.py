"""Router Agent Graph - intelligently routes requests to specialized agents."""

import logging
from typing import Optional, TypedDict, Annotated
import uuid

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue import EventQueue
from langgraph.graph import StateGraph, END, add_messages
from langgraph.graph.state import RunnableConfig
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import InMemorySaver
from app.core.config import settings
from app.agents.tools.delegate_to_agent import delegate_to_agent
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)
from a2a.utils import (
    new_task,
    new_text_artifact
)

from app.models.router_agent_model import AgentNodeState

checkpointer = InMemorySaver()
SYSTEM_PROMPT = """You are an intelligent Router Agent that analyzes user queries and delegates them to the most appropriate specialized agent.

## CRITICAL RULE: ONE DELEGATION PER QUERY
**IMPORTANT**: For each user query, you should delegate to ONLY ONE agent. After receiving a response from that agent, you must:
1. Analyze if the response adequately answers the user's query
2. If yes → Present the final answer to the user (DO NOT delegate again)
3. If no → Explain what information is missing and ask the user for clarification

**NEVER delegate to multiple agents for the same query unless explicitly requested by the user.**

## Available Agents

### 1. Data Sources Agent(data_sources_agent)
**Purpose**: Handles queries related to internal documents, knowledge bases, and vector databases.
**Capabilities**:
- Ingest documents into the vector database
- Query vector databases for semantic search
- Retrieve information from indexed documents
- Search through RAG (Retrieval-Augmented Generation) data sources
- Handle questions about internal knowledge and documentation

**Use this agent for**:
- Questions about internal documents or knowledge base
- Requests to search through indexed content
- Document ingestion or vector database operations
- Queries requiring semantic search through stored data
- Information retrieval from pre-existing data sources

### 2. Internet Search Agent(internet_search_agent)  
**Purpose**: Handles queries requiring real-time web information and current events.
**Capabilities**:
- Search the internet using Tavily API
- Find current events and breaking news
- Research general topics from web sources
- Gather real-time information
- Access publicly available web data

**Use this agent for**:
- Current events, news, or recent developments
- General web research and fact-finding
- Information not likely to be in internal databases
- Real-time data or statistics
- External information beyond organizational knowledge

## Your Routing Logic

1. **Check Previous Responses First**:
   - Look at the conversation history - have you already delegated this query?
   - If you see a ToolMessage response from a previous delegation → Analyze and present that response
   - DO NOT delegate the same query to another agent

2. **For New Queries Only**:
   - Analyze what the user is asking for
   - Choose the SINGLE most appropriate agent based on the query type
   - Delegate once and wait for the response

3. **After Receiving Agent Response (ToolMessage)**:
   - The response will be in the conversation as a ToolMessage
   - Analyze the response content thoroughly
   - If it answers the query → Synthesize and present the final answer to the user
   - If it doesn't fully answer → Tell the user what was found and what's missing
   - DO NOT automatically delegate to another agent

4. **Ask for User Clarification When**:
   - Before delegation: The query is ambiguous about which data source to use
   - After delegation: The agent's response doesn't fully address the query

## Response Guidelines

### When Delegating (First Time Only):
- Use the delegate_to_agent tool with:
  - agent_name: Either 'data_sources_agent' or 'internet_search_agent' 
  - query: The user's original query

### After Receiving Agent Response:
- **DO NOT delegate again** - work with the response you received
- If the response contains relevant information → Provide a clear, synthesized answer
- If the response indicates no data found → Inform the user clearly
- Never loop between agents for the same query

### Final Answer Format:
- Summarize the key findings from the agent's response
- Present the information clearly and concisely
- Do not mention internal routing or agent names unless relevant
- Focus on answering the user's actual question

Remember: Route ONCE per query, analyze the response, then provide a final answer. Breaking this rule causes infinite loops."""

STATE_OUTPUT_STRUCTURED_OUTPUT = """
Determine the current state of the conversation based on the user query and conversation progress.

You must output one of the following states:

**input_required**: The conversation requires additional input or clarification from the user.
  - Use when: The query is ambiguous, lacks context, or requires the user to choose between options
  - Example: User asked about "documents" but didn't specify which documents or data source

**completed**: The conversation has concluded successfully and the user's query has been fully answered.
  - Use when: The query has been answered, the requested action has been completed, or the final response has been delivered
  - Example: User asked a question and received a complete answer with no follow-up needed

**working**: The conversation is actively being processed and not yet complete.
  - Use when: Tools are being called, agents are being delegated to, or processing is still in progress
  - Example: A tool call has been made but hasn't returned results yet, or an agent is still working on the request
"""

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    agent_state: str = "working"
    current_agent: Optional[str] = None
    context_id : str = str(uuid.uuid4())
    task_id: Optional[str] = None


def should_continue(state: AgentState):
    """Route to tools or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def create_router_agent_graph():
    """Create router agent graph with delegation capabilities."""
    from app.agents.llm_models import data_sources_agent_llm

    # Use the delegate_to_agent function tool
    tools = [delegate_to_agent]

    async def agent_node(state: AgentState):
        """Agent reasoning node."""
        bound_model = data_sources_agent_llm.bind_tools(tools)
        model_with_structured_output = data_sources_agent_llm.with_structured_output(AgentNodeState)
        logger.info(f"Router agent processing messages: {state['messages']}")
        try:

            response = await bound_model.ainvoke(
                [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
            )
            agent_state = "working"
            if hasattr(response, "tool_calls") and len(response.tool_calls) == 0:
                agent_state : AgentNodeState = await model_with_structured_output.ainvoke(
                    [SystemMessage(content=STATE_OUTPUT_STRUCTURED_OUTPUT)] + state["messages"] + [response, HumanMessage(content="")]
                )
                agent_state = agent_state.state

        except Exception as e:
            logger.error(f"Error in router agent: {e}")
            return {"messages": [SystemMessage(content=f"Error in router agent: {e}")], "state": "completed"}

        return {"messages": [response], "agent_state": agent_state}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(tools))

    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent", should_continue, {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")

    return workflow.compile(checkpointer=checkpointer)


def get_router_agent_card():
    """Get the agent card for the router agent."""
    return AgentCard(
        name="Router Agent",
        description="An intelligent routing agent that analyzes queries and delegates them to specialized agents",
        url=f"http://{settings.host}:{settings.port}/router-agent",
        capabilities=AgentCapabilities(),
        skills=[
            AgentSkill(
                id="route-query",
                description="Analyze queries and route them to the appropriate specialized agent - Data Sources Agent or Internet Search Agent",
                name="Route Query",
                tags=["routing", "delegation"],
            ),
        ],
        default_input_modes=["text"],
        default_output_modes=["text"],
        version="1.0.0",
    )


class RouterAgentExecutor(AgentExecutor):
    def __init__(self):
        super().__init__()
        self._agent = None

    @property
    def agent(self):
        """Lazy initialization of agent graph."""
        if self._agent is None:
            self._agent = create_router_agent_graph()
        return self._agent

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        query = context.get_user_input()
        task = context.current_task
        message = context.message
        
        if not task:
            task = new_task(message)
            await event_queue.enqueue_event(task)
            
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config=RunnableConfig(configurable={"thread_id": task.context_id})
        )
        
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                append=False,
                context_id=task.context_id,
                task_id=task.id,
                last_chunk=True,
                artifact=new_text_artifact(
                    name='response',
                    description='Response from router agent.',
                    text=result['messages'][-1].content,
                ),
            )
        )
        
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                status=TaskStatus(state=TaskState.completed),
                final=True,
                context_id=task.context_id,
                task_id=task.id,
            )
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("cancel not supported")
