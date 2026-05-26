## 1. Introduction

This multi-agent system uses two protocols:

1. **MCP (Model Context Protocol)**: Standardized tool integration for agents
2. **A2A (Agent-to-Agent) Protocol**: Inter-agent communication protocol

## 2. System Components

### Router Agent
- Analyzes queries and delegates to appropriate specialized agent
- Enforces one delegation per query to prevent loops
- Synthesizes responses from other agents

### Data Sources Agent
- Queries vector database for semantic search
- Ingests documents into Qdrant
- Named for future extensibility to multiple data sources

### Internet Search Agent
- Searches web using Tavily API
- Provides real-time information not in internal databases

## 3. MCP (Model Context Protocol) Implementation

### Tool Signatures

```python
# MCP server setup
mcp = FastMCP("rag-tool", port=8092)

@mcp.tool(
    name="query-vector-db", 
    title="Query vector database", 
    description="Query the vector database for relevant documents"
)
def query_vector_db(query: str, top_k: int = 10) -> str:
    # Returns JSON with search results

@mcp.tool(name="ingest-document", title="Ingest document")
def ingest_document(
    document: str, 
    metadata: Dict[str, Any] = None,
    chunk_size: int = 500
) -> str:
    # Returns success message with chunk count
```

### LangGraph Integration

```python
# ToolsService discovers and provides tools to agents
class ToolsService(metaclass=ToolServiceMeta):
    async def connect_to_mcp_servers(self):
        # Start MCP server subprocess
        rag_process = subprocess.Popen([sys.executable, rag_tool_path])
        
        # Configure MCP clients
        config = {
            "rag-tool": {"transport": "streamable_http", "url": settings.rag_tool_mcp_url},
            "tavily": {"transport": "streamable_http", "url": settings.tavily_mcp_url},
        }
        
        # Discover tools
        self._mcp_client = MultiServerMCPClient(config)
        tools = await self._mcp_client.get_tools()
        self.add_tools(tools)

# Agent uses tools in LangGraph workflow
async def agent_node(state: AgentState):
    tools = ToolsService().get_tools_by_names(["query-vector-db", "ingest-document"])
    bound_model = data_sources_agent_llm.bind_tools(tools)
    response = await bound_model.ainvoke(
        [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    )
    return {"messages": [response]}

# Tool execution node
workflow.add_node("tools", ToolNode(tools))
```

## 4. A2A (Agent-to-Agent) Protocol Implementation

### Agent Cards

Agents advertise capabilities through agent cards:

```python
def get_data_sources_agent_card():
    return AgentCard(
        name="Data Sources Agent",
        url=f"http://{settings.host}:{settings.port}/datasources-agent",
        skills=[
            AgentSkill(id="ingest-document", name="Ingest document"),
            AgentSkill(id="query-vector-db", name="Query vector database"),
        ],
        default_input_modes=["text"],
        default_output_modes=["text"],
    )
```

### Delegation Tool

Router delegates to other agents via `delegate_to_agent`:

```python
@tool
async def delegate_to_agent(
    agent_name: str,
    query: str,
    runtime: Annotated[ToolRuntime, InjectedToolArg]
) -> Command:
    # Get agent card
    agent_card = get_data_sources_agent_card()  # or internet_search_agent_card
    
    # Create A2A request
    req = SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams.model_validate({
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": query}],
                "messageId": message_id,
            }
        })
    )
    
    # Send via A2A client
    a2a_client = A2AClient(httpx_client, agent_card, url=agent_card.url)
    res = await a2a_client.send_message(req)
    
    # Extract response from Task
    if task.status.state == TaskState.completed:
        response_text = task.artifacts[0].parts[0].text
```

## 5. Request Flow

Example: User asks "What is Graph RAG?"

1. **User → Router Agent**
```python
await agent.ainvoke(
    {"messages": [HumanMessage(content="What is Graph RAG?")]},
    config=RunnableConfig(configurable={"thread_id": context_id})
)
```

2. **Router analyzes and delegates**
   - Router determines this needs Data Sources Agent
   - Calls `delegate_to_agent("data_sources_agent", "What is Graph RAG?")`

3. **A2A communication**
   - Creates SendMessageRequest with query
   - Sends to Data Sources Agent via A2A protocol

4. **Data Sources Agent processes**
   - Receives query via RequestContext
   - Uses MCP tool `query_vector_db` to search Qdrant
   - Tool generates embeddings and searches vector database

5. **Response flows back**
   - Data Sources packages response in TaskArtifactUpdateEvent
   - Router receives via ToolMessage
   - Router synthesizes and returns final answer to user

## 6. Agent Executors and FastAPI Integration

### Agent Executors with LangGraph

```python
def create_router_agent_graph():
    """Create router agent graph with delegation capabilities."""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)  # Reasoning node
    workflow.add_node("tools", ToolNode(tools))  # Tool execution
    
    # Set entry point and routing
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent", 
        should_continue,  # Decides tools or END
        {"tools": "tools", END: END}
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile(checkpointer=checkpointer)

class RouterAgentExecutor(AgentExecutor):
    def __init__(self):
        super().__init__()
        self._agent = None

    @property
    def agent(self):
        if self._agent is None:
            self._agent = create_router_agent_graph()
        return self._agent

    async def execute(self, context: RequestContext, event_queue: EventQueue):
        query = context.get_user_input()
        task = context.current_task or new_task(context.message)
        
        result = await self.agent.ainvoke(
            {"messages": [HumanMessage(content=query)]},
            config=RunnableConfig(configurable={"thread_id": task.context_id})
        )
        
        # Send response event
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                artifact=new_text_artifact(
                    name='response',
                    text=result['messages'][-1].content,
                )
            )
        )
```

### FastAPI Registration

```python
# main.py - Agent registration in FastAPI app

# Create agent components
data_sources_agent_card = get_data_sources_agent_card()
data_sources_agent_executor = DataSourcesAgentExecutor()
data_sources_request_handler = DefaultRequestHandler(
    agent_executor=data_sources_agent_executor,
    task_store=InMemoryTaskStore(),
)

# Register with A2A application
A2AFastAPIApplication(
    agent_card=data_sources_agent_card, 
    http_handler=data_sources_request_handler
).add_routes_to_app(
    app,
    agent_card_url="/datasources-agent/.well-known/a2a",
    rpc_url="/datasources-agent",
)

# Same pattern for Router and Internet Search agents
```

## 7. Usage Example

```python
# Direct agent usage
agent = create_router_agent_graph()
result = await agent.ainvoke(
    {
        "messages": [HumanMessage(content="What is Graph RAG?")],
        "context_id": str(uuid.uuid4()),
    },
    config=RunnableConfig(configurable={"thread_id": context_id})
)

# A2A client usage
card_resolver = A2ACardResolver(client, "http://localhost:8080", "/agent/.well-known/a2a")
card = await card_resolver.get_agent_card()
a2a_client = A2AClient(client, card, url=card.url)

req = SendMessageRequest(
    id=str(uuid.uuid4()),
    params=MessageSendParams.model_validate({
        'message': {
            'role': 'user',
            'parts': [{'type': 'text', 'text': query}],
            'messageId': message_id,
        }
    })
)
res = await a2a_client.send_message(req)
```
