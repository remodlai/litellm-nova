# Pydantic AI Integration Guide for LiteLLM Agentic Routes

This guide provides comprehensive information on using pydantic-ai to build `/chat/agentic` routes in LiteLLM that will run as Temporal workflows with MCP server integration.

## Table of Contents
1. [Agent Creation & Configuration](#agent-creation--configuration)
2. [MCP Server Integration](#mcp-server-integration)
3. [Agentic Loop & Execution](#agentic-loop--execution)
4. [Session Management](#session-management)
5. [Structured Outputs](#structured-outputs)
6. [Error Handling & Retries](#error-handling--retries)
7. [Dependencies & RunContext](#dependencies--runcontext)
8. [FastAPI Integration Patterns](#fastapi-integration-patterns)
9. [Complete Example Implementation](#complete-example-implementation)
10. [Best Practices & Common Pitfalls](#best-practices--common-pitfalls)

---

## 1. Agent Creation & Configuration

### Basic Agent with Custom OpenAI-Compatible Endpoint

Pydantic AI supports any OpenAI-compatible endpoint through the `OpenAIChatModel` and `OpenAIProvider` classes:

```python
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

# Create a model pointing to your custom endpoint
model = OpenAIChatModel(
    'model_name',  # Your model identifier
    provider=OpenAIProvider(
        base_url='https://your-openai-compatible-endpoint.com',
        api_key='your-api-key'
    ),
)

# Create an agent with the custom model
agent = Agent(model, system_prompt='Be a helpful assistant.')
```

### Advanced Configuration with Custom Profile

For providers that require specific settings (e.g., disabling strict tool definitions):

```python
from pydantic_ai import Agent, InlineDefsJsonSchemaTransformer
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.profiles.openai import OpenAIModelProfile
from pydantic_ai.providers.openai import OpenAIProvider

model = OpenAIChatModel(
    'model_name',
    provider=OpenAIProvider(
        base_url='https://your-endpoint.com',
        api_key='your-api-key'
    ),
    profile=OpenAIModelProfile(
        json_schema_transformer=InlineDefsJsonSchemaTransformer,
        openai_supports_strict_tool_definition=False  # Disable strict mode
    )
)

agent = Agent(model)
```

### Model Settings

Configure model behavior with `ModelSettings`:

```python
from pydantic_ai.settings import ModelSettings

agent = Agent(
    model,
    system_prompt='You are a helpful assistant.',
    settings=ModelSettings(
        max_steps=10,          # Maximum agentic loop iterations
        temperature=0.7,       # Sampling temperature (0.0 for deterministic)
        max_tokens=2000,       # Maximum tokens in response
        timeout=60.0,          # Request timeout in seconds
    )
)
```

**Settings Precedence** (highest to lowest):
1. Run-time overrides (passed to `run()`, `run_sync()`, `run_stream()`)
2. Agent-level defaults (set during `Agent` initialization)
3. Model-level defaults (set during model instance creation)

### System Prompts

System prompts can be static strings or dynamic functions:

```python
# Static system prompt
agent = Agent('openai:gpt-4', system_prompt='Be concise and accurate.')

# Dynamic system prompt with dependencies
from pydantic_ai import RunContext

@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    # Fetch dynamic data from external source
    response = await ctx.deps.http_client.get('https://api.example.com/context')
    return f'You are an assistant. Context: {response.text}'
```

---

## 2. MCP Server Integration

### Basic MCP Server Setup

Pydantic AI provides `MCPServerSSE` for Server-Sent Events (SSE) based MCP servers:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

# Create MCP server connection
server = MCPServerSSE('http://localhost:3001/sse')

# Create agent with MCP toolset
agent = Agent('openai:gpt-4', toolsets=[server])
```

### Multiple MCP Servers with Tool Prefixes

Avoid naming conflicts when using multiple MCP servers:

```python
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerSSE

# Create servers with different prefixes
weather_server = MCPServerSSE(
    'http://localhost:3001/sse',
    tool_prefix='weather'  # Tools prefixed with 'weather_'
)

filesystem_server = MCPServerSSE(
    'http://localhost:3002/sse',
    tool_prefix='fs'  # Tools prefixed with 'fs_'
)

# Both servers can have a 'get_data' tool, exposed as:
# - 'weather_get_data'
# - 'fs_get_data'
agent = Agent('openai:gpt-4', toolsets=[weather_server, filesystem_server])
```

### Tool Discovery & Execution

MCP servers automatically expose their tools to the agent:

1. **Tool Discovery**: When an agent is created with MCP toolsets, tools are automatically discovered from the MCP server
2. **Tool Calling**: The LLM can call any discovered tool by name
3. **Tool Execution**: The agent handles the execution and returns results to the LLM
4. **Tool Results**: Results are formatted and added to the conversation history

### Custom Tool Processing

You can intercept and process tool calls:

```python
from pydantic_ai.mcp import MCPServerSSE

async def process_tool_call(ctx, direct_call_func, tool_name, tool_args):
    # Custom pre-processing
    print(f"Calling tool: {tool_name} with args: {tool_args}")

    # Execute the tool
    result = await direct_call_func(tool_name, tool_args)

    # Custom post-processing
    print(f"Tool result: {result}")
    return result

server = MCPServerSSE(
    'http://localhost:3001/sse',
    process_tool_call=process_tool_call
)
```

---

## 3. Agentic Loop & Execution

### How agent.run() Works

The agent operates in a multi-step loop:

1. **Initial Request**: User prompt is sent to the model
2. **Model Response**: Model either:
   - Returns final output, OR
   - Requests tool call(s)
3. **Tool Execution**: If tools requested, agent executes them
4. **Tool Results**: Results are added to conversation
5. **Loop**: Steps 2-4 repeat until:
   - Model returns final output
   - `max_steps` limit reached
   - Error occurs

```python
# Async execution
result = await agent.run('What is the weather in SF?')
print(result.output)  # Final output

# Sync execution (uses asyncio.run internally)
result = agent.run_sync('What is the weather in SF?')
print(result.output)
```

### Streaming Responses

Stream events as they occur:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')

async def stream_example():
    # Stream all events
    async for event in agent.run_stream_events('Tell me a story'):
        print(f"Event type: {event.type}")
        if hasattr(event, 'content'):
            print(f"Content: {event.content}")
```

### Manual Control with agent.iter()

For fine-grained control over execution:

```python
from pydantic_ai import Agent
from pydantic_graph import End

agent = Agent('openai:gpt-4')

async def manual_control():
    async with agent.iter('What is the capital of France?') as agent_run:
        node = agent_run.next_node
        all_nodes = [node]

        # Manually drive iteration
        while not isinstance(node, End):
            # Inspect or modify before execution
            print(f"Current node type: {type(node).__name__}")
            node = await agent_run.next(node)
            all_nodes.append(node)

        print(f"Final output: {agent_run.result.output}")
        return agent_run.result
```

### Conversation History Management

Maintain context across multiple runs:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4', system_prompt='Be a helpful assistant.')

# First interaction
result1 = agent.run_sync('Who was Albert Einstein?')
print(result1.output)

# Continue conversation with history
result2 = agent.run_sync(
    'What was his most famous equation?',
    message_history=result1.new_messages()  # Pass only new messages
)
print(result2.output)

# Access all messages in conversation
all_messages = result2.all_messages()
print(f"Total messages: {len(all_messages)}")
```

**Key Methods**:
- `result.new_messages()` - Only messages from this run (for continuation)
- `result.all_messages()` - Complete message history
- `result.all_messages_json()` - Serialized message history

---

## 4. Session Management

### Agent Reusability

**Yes, Agent instances can and should be reused across conversations.**

Benefits:
- Single model connection
- Shared configuration
- Lower memory overhead
- Better performance

```python
from pydantic_ai import Agent

# Create agent once (e.g., at application startup)
agent = Agent('openai:gpt-4', system_prompt='Be helpful.')

# Use for multiple users/sessions
async def handle_user_message(user_id: str, message: str, history: list):
    result = await agent.run(
        message,
        message_history=history,  # Session-specific history
        deps=get_user_deps(user_id)  # User-specific dependencies
    )
    return result

# Each session maintains its own history
user1_history = []
user2_history = []

result1 = await handle_user_message('user1', 'Hello', user1_history)
user1_history.extend(result1.new_messages())

result2 = await handle_user_message('user2', 'Hi there', user2_history)
user2_history.extend(result2.new_messages())
```

### Temporal Workflow Pattern

For long-running agentic sessions:

```python
from temporalio import workflow
from pydantic_ai import Agent
from typing import List

# Global agent (initialized once)
AGENT = Agent('openai:gpt-4')

@workflow.defn
class AgenticChatWorkflow:
    def __init__(self):
        self.message_history = []

    @workflow.run
    async def run(self, session_id: str) -> str:
        return f"Session {session_id} started"

    @workflow.signal
    async def add_message(self, message: str):
        # Run agent with accumulated history
        result = await AGENT.run(
            message,
            message_history=self.message_history,
            deps=await self._get_deps()
        )

        # Update history for next interaction
        self.message_history.extend(result.new_messages())

        # Store result or emit event
        await self._store_result(result)

    @workflow.query
    def get_history(self) -> List[dict]:
        return [msg.model_dump() for msg in self.message_history]

    async def _get_deps(self):
        # Get workflow-specific dependencies
        return MyDeps(...)

    async def _store_result(self, result):
        # Store in Temporal or external DB
        pass
```

---

## 5. Structured Outputs

### Basic Structured Output

Define output types using Pydantic models:

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class UserInfo(BaseModel):
    name: str
    age: int
    email: str

agent = Agent('openai:gpt-4', output_type=UserInfo)

result = agent.run_sync('Extract info: John Doe, 30 years old, john@example.com')
print(result.output.name)  # 'John Doe'
print(result.output.age)   # 30
```

### Multiple Output Types

Handle different response types:

```python
from pydantic import BaseModel
from pydantic_ai import Agent, ToolOutput

class Fruit(BaseModel):
    name: str
    color: str

class Vehicle(BaseModel):
    name: str
    wheels: int

agent = Agent(
    'openai:gpt-4',
    output_type=[
        ToolOutput(Fruit, name='return_fruit'),
        ToolOutput(Vehicle, name='return_vehicle'),
    ],
)

result1 = agent.run_sync('What is a banana?')
print(result1.output)  # Fruit(name='banana', color='yellow')

result2 = agent.run_sync('What is a car?')
print(result2.output)  # Vehicle(name='car', wheels=4)
```

### Tool Call Inspection

Access tool calls from results:

```python
result = await agent.run('Get weather for SF and NY')

# Inspect tool calls made during the run
for message in result.all_messages():
    if message.kind == 'request':
        for part in message.parts:
            if part.part_kind == 'tool-call':
                print(f"Tool: {part.tool_name}")
                print(f"Args: {part.args_as_dict()}")
```

### Supported Output Types

- **Scalar types**: `str`, `int`, `float`, `bool`
- **Collections**: `list`, `dict`, `set`
- **Type hints**: `List[int]`, `Dict[str, Any]`
- **TypedDict**: Structured dictionaries
- **Dataclasses**: Standard Python dataclasses
- **Pydantic models**: Full Pydantic v2 support
- **Unions**: `str | int`, `Union[TypeA, TypeB]`

---

## 6. Error Handling & Retries

### ModelRetry Exception

Request the model to retry with feedback:

```python
from pydantic_ai import Agent, RunContext, ModelRetry

agent = Agent('openai:gpt-4')

@agent.tool(retries=2)  # Retry up to 2 times
def get_user_by_name(ctx: RunContext, name: str) -> int:
    """Get a user's ID from their full name."""
    user_id = ctx.deps.database.get_user(name)
    if user_id is None:
        # Tell model to retry with better input
        raise ModelRetry(
            f'No user found with name {name!r}. '
            'Please provide their full name (first and last).'
        )
    return user_id
```

### Validation Errors

Pydantic automatically handles validation errors:

```python
from pydantic_ai import Agent

@agent.tool
def calculate_age(birth_year: int) -> int:
    """Calculate age from birth year."""
    if birth_year < 1900 or birth_year > 2024:
        # This will be automatically caught and sent back to model
        raise ValueError('Birth year must be between 1900 and 2024')
    return 2024 - birth_year
```

### Capturing Messages for Debugging

Use `capture_run_messages` to debug failures:

```python
from pydantic_ai import Agent, ModelRetry, UnexpectedModelBehavior, capture_run_messages

agent = Agent('openai:gpt-4')

@agent.tool_plain
def flaky_tool(size: int) -> int:
    if size != 42:
        raise ModelRetry('Please try again with size 42.')
    return size ** 3

with capture_run_messages() as messages:
    try:
        result = agent.run_sync('Get volume of box with size 6.')
    except UnexpectedModelBehavior as e:
        print(f'Error: {e}')
        print(f'Cause: {e.__cause__}')
        print(f'Messages exchanged: {messages}')
    else:
        print(result.output)
```

### Retry Configuration

Configure retry behavior at different levels:

```python
from pydantic_ai import Agent

# Agent-level default retries
agent = Agent('openai:gpt-4', retries=3)

# Tool-level retries (overrides agent default)
@agent.tool(retries=5)
def critical_tool(arg: str) -> str:
    """This tool gets more retry attempts."""
    return f"Processed: {arg}"

# Run-level retry limits
result = agent.run_sync(
    'Process data',
    usage_limits={'max_retries': 2}  # Override for this run
)
```

---

## 7. Dependencies & RunContext

### Defining Dependencies

Use dependencies for database connections, API clients, configuration:

```python
from dataclasses import dataclass
import httpx
from pydantic_ai import Agent, RunContext

@dataclass
class MyDeps:
    api_key: str
    http_client: httpx.AsyncClient
    database: DatabaseConnection
    user_id: str

agent = Agent(
    'openai:gpt-4',
    deps_type=MyDeps,  # Specify dependency type
)
```

### Accessing Dependencies

Dependencies are available in system prompts, tools, and validators:

```python
# In system prompt
@agent.system_prompt
async def get_system_prompt(ctx: RunContext[MyDeps]) -> str:
    user = await ctx.deps.database.get_user(ctx.deps.user_id)
    return f'You are assisting {user.name}. Their preferences: {user.preferences}'

# In tools
@agent.tool
async def search_api(ctx: RunContext[MyDeps], query: str) -> str:
    """Search external API."""
    response = await ctx.deps.http_client.get(
        'https://api.example.com/search',
        params={'q': query},
        headers={'Authorization': f'Bearer {ctx.deps.api_key}'}
    )
    return response.text

# In validators
@agent.output_validator
async def validate_output(ctx: RunContext[MyDeps], output: str) -> str:
    if not await ctx.deps.database.is_valid_output(output):
        raise ModelRetry('Output did not pass validation.')
    return output
```

### Passing Dependencies at Runtime

Dependencies are passed when running the agent:

```python
async def handle_request(user_id: str, message: str):
    async with httpx.AsyncClient() as client:
        deps = MyDeps(
            api_key='secret-key',
            http_client=client,
            database=get_database(),
            user_id=user_id
        )

        result = await agent.run(message, deps=deps)
        return result.output
```

### RunContext Attributes

The `RunContext` provides additional context:

```python
from pydantic_ai import RunContext

@agent.tool
async def my_tool(ctx: RunContext[MyDeps], arg: str) -> str:
    # Access dependencies
    data = await ctx.deps.database.query(arg)

    # Access tool metadata
    print(f"Tool name: {ctx.tool_name}")

    # Access run metadata
    print(f"Retry attempt: {ctx.retry}")

    return f"Result: {data}"
```

---

## 8. FastAPI Integration Patterns

### Basic FastAPI Endpoint

Create a streaming endpoint for the agent:

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic_ai import Agent
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.ag_ui import AGUIAdapter

agent = Agent('openai:gpt-4', instructions='Be helpful and concise!')

app = FastAPI()

@app.post('/agent')
async def run_agent(request: Request):
    # Get accept header (defaults to SSE)
    accept = request.headers.get('accept', SSE_CONTENT_TYPE)

    # Parse request body into agent input
    run_input = AGUIAdapter.build_run_input(await request.body())

    # Create adapter for the agent
    adapter = AGUIAdapter(agent=agent, run_input=run_input, accept=accept)

    # Run and stream events
    event_stream = adapter.run_stream()
    sse_stream = adapter.encode_stream(event_stream)

    return StreamingResponse(sse_stream, media_type=accept)
```

### With Dependencies and State

Handle user-specific context:

```python
from dataclasses import dataclass, replace
from fastapi import FastAPI, Request, Depends
from pydantic_ai import Agent
from pydantic_ai.ui.ag_ui import AGUIAdapter

@dataclass
class RequestDeps:
    user_id: str
    database: DatabaseConnection

async def get_deps(request: Request) -> RequestDeps:
    # Extract from headers/JWT/etc
    user_id = request.headers.get('X-User-ID')
    return RequestDeps(
        user_id=user_id,
        database=get_database()
    )

agent = Agent('openai:gpt-4', deps_type=RequestDeps)

app = FastAPI()

@app.post('/agent')
async def run_agent(
    request: Request,
    deps: RequestDeps = Depends(get_deps)
):
    run_input = AGUIAdapter.build_run_input(await request.body())

    # Pass dependencies to adapter
    adapter = AGUIAdapter(
        agent=agent,
        run_input=run_input,
        deps=deps,
        accept=request.headers.get('accept', SSE_CONTENT_TYPE)
    )

    event_stream = adapter.run_stream()
    sse_stream = adapter.encode_stream(event_stream)

    return StreamingResponse(sse_stream, media_type=SSE_CONTENT_TYPE)
```

### Non-Streaming Response

For clients that don't support streaming:

```python
from fastapi import FastAPI
from pydantic import BaseModel
from pydantic_ai import Agent

class ChatRequest(BaseModel):
    message: str
    history: list[dict] | None = None

class ChatResponse(BaseModel):
    output: str
    usage: dict

agent = Agent('openai:gpt-4')

app = FastAPI()

@app.post('/chat', response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Convert history if provided
    message_history = None
    if request.history:
        message_history = [
            # Convert dict history to ModelMessage objects
            agent._message_from_dict(msg) for msg in request.history
        ]

    result = await agent.run(
        request.message,
        message_history=message_history
    )

    return ChatResponse(
        output=result.output,
        usage={
            'requests': result.usage().requests,
            'request_tokens': result.usage().request_tokens,
            'response_tokens': result.usage().response_tokens,
        }
    )
```

---

## 9. Complete Example Implementation

Here's a complete example for an agentic route handler:

```python
"""
Complete example: Agentic chat route for LiteLLM
Integrates with Temporal workflows and MCP servers
"""
from dataclasses import dataclass, replace
from typing import List
import httpx
from temporalio import workflow
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse

from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings
from pydantic_ai.mcp import MCPServerSSE
from pydantic_ai.ui import SSE_CONTENT_TYPE
from pydantic_ai.ui.ag_ui import AGUIAdapter

# ============================================================================
# Configuration
# ============================================================================

@dataclass
class AgentDeps:
    """Dependencies injected into agent tools and prompts."""
    user_id: str
    session_id: str
    http_client: httpx.AsyncClient
    # Add your database, cache, etc.

# ============================================================================
# Agent Setup
# ============================================================================

def create_agent(
    model_endpoint: str,
    model_name: str,
    api_key: str,
    mcp_servers: List[str] | None = None
) -> Agent:
    """Create a configured agent with custom model and MCP servers."""

    # Configure custom OpenAI-compatible model
    model = OpenAIChatModel(
        model_name,
        provider=OpenAIProvider(
            base_url=model_endpoint,
            api_key=api_key
        ),
        settings=ModelSettings(
            max_steps=10,
            temperature=0.7,
            timeout=60.0,
        )
    )

    # Setup MCP servers if provided
    toolsets = []
    if mcp_servers:
        for i, server_url in enumerate(mcp_servers):
            toolsets.append(
                MCPServerSSE(
                    server_url,
                    tool_prefix=f'mcp{i}'  # Avoid collisions
                )
            )

    # Create agent
    agent = Agent(
        model,
        deps_type=AgentDeps,
        system_prompt='You are a helpful AI assistant.',
        retries=3,  # Default retry count for tools
    )

    # Add tools
    @agent.tool
    async def search_database(
        ctx: RunContext[AgentDeps],
        query: str
    ) -> str:
        """Search internal database for information."""
        # Access dependencies
        user_id = ctx.deps.user_id

        # Perform search (example)
        # result = await ctx.deps.database.search(query, user_id)
        result = f"Results for '{query}' (user: {user_id})"
        return result

    @agent.tool(retries=5)
    async def call_external_api(
        ctx: RunContext[AgentDeps],
        endpoint: str,
        params: dict
    ) -> str:
        """Call external API endpoint."""
        try:
            response = await ctx.deps.http_client.get(
                f'https://api.example.com/{endpoint}',
                params=params
            )
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            raise ModelRetry(f'API call failed: {e}. Please retry.')

    # Add output validator
    @agent.output_validator
    async def validate_response(
        ctx: RunContext[AgentDeps],
        output: str
    ) -> str:
        """Validate agent output before returning."""
        # Example: Check for prohibited content
        if 'UNSAFE' in output.upper():
            raise ModelRetry('Response contains unsafe content. Rephrase.')
        return output

    return agent

# ============================================================================
# Temporal Workflow
# ============================================================================

@workflow.defn
class AgenticChatWorkflow:
    """Long-running agentic chat session managed by Temporal."""

    def __init__(self):
        self.message_history = []
        self.agent = None

    @workflow.run
    async def run(
        self,
        session_id: str,
        model_endpoint: str,
        model_name: str,
        api_key: str,
        mcp_servers: List[str] | None = None
    ) -> str:
        """Initialize workflow."""
        # Create agent for this session
        self.agent = create_agent(
            model_endpoint,
            model_name,
            api_key,
            mcp_servers
        )
        return f"Session {session_id} initialized"

    @workflow.signal
    async def process_message(self, user_id: str, message: str):
        """Process a user message."""
        async with httpx.AsyncClient() as client:
            deps = AgentDeps(
                user_id=user_id,
                session_id=workflow.info().workflow_id,
                http_client=client
            )

            # Run agent with accumulated history
            result = await self.agent.run(
                message,
                message_history=self.message_history,
                deps=deps
            )

            # Update history for next interaction
            self.message_history.extend(result.new_messages())

            # Emit event with result
            await workflow.execute_activity(
                'store_result',
                args=[result.output, result.usage().model_dump()]
            )

    @workflow.query
    def get_history(self) -> List[dict]:
        """Get conversation history."""
        return [
            {
                'role': msg.kind,
                'content': str(msg),
            }
            for msg in self.message_history
        ]

    @workflow.query
    def get_message_count(self) -> int:
        """Get total message count."""
        return len(self.message_history)

# ============================================================================
# FastAPI Routes
# ============================================================================

app = FastAPI(title="LiteLLM Agentic Routes")

# Global agent instance (for non-workflow use)
AGENT: Agent | None = None

@app.on_event("startup")
async def startup():
    """Initialize agent on startup."""
    global AGENT
    AGENT = create_agent(
        model_endpoint='http://localhost:8000/v1',
        model_name='gpt-4',
        api_key='test-key',
        mcp_servers=['http://localhost:3001/sse']
    )

async def get_deps(request: Request) -> AgentDeps:
    """Extract dependencies from request."""
    user_id = request.headers.get('X-User-ID', 'anonymous')
    session_id = request.headers.get('X-Session-ID', 'default')

    # Create HTTP client (should be pooled in production)
    http_client = httpx.AsyncClient()

    return AgentDeps(
        user_id=user_id,
        session_id=session_id,
        http_client=http_client
    )

@app.post('/chat/agentic/stream')
async def agentic_stream(
    request: Request,
    deps: AgentDeps = Depends(get_deps)
):
    """Streaming agentic chat endpoint."""
    if AGENT is None:
        raise HTTPException(500, "Agent not initialized")

    try:
        # Parse request
        accept = request.headers.get('accept', SSE_CONTENT_TYPE)
        run_input = AGUIAdapter.build_run_input(await request.body())

        # Create adapter
        adapter = AGUIAdapter(
            agent=AGENT,
            run_input=run_input,
            deps=deps,
            accept=accept
        )

        # Stream events
        event_stream = adapter.run_stream()
        sse_stream = adapter.encode_stream(event_stream)

        return StreamingResponse(sse_stream, media_type=accept)

    finally:
        # Cleanup
        await deps.http_client.aclose()

@app.post('/chat/agentic')
async def agentic_chat(
    request: Request,
    deps: AgentDeps = Depends(get_deps)
):
    """Non-streaming agentic chat endpoint."""
    if AGENT is None:
        raise HTTPException(500, "Agent not initialized")

    try:
        body = await request.json()
        message = body.get('message')
        history = body.get('history', [])

        if not message:
            raise HTTPException(400, "Missing 'message' field")

        # Convert history
        message_history = None
        if history:
            # Parse history into ModelMessage objects
            # (Implementation depends on your history format)
            pass

        # Run agent
        result = await AGENT.run(
            message,
            message_history=message_history,
            deps=deps
        )

        return {
            'output': result.output,
            'usage': result.usage().model_dump(),
            'new_messages': [
                {'role': msg.kind, 'content': str(msg)}
                for msg in result.new_messages()
            ]
        }

    finally:
        await deps.http_client.aclose()

# ============================================================================
# Temporal Workflow Endpoints
# ============================================================================

@app.post('/chat/agentic/session/start')
async def start_session(
    user_id: str,
    model_endpoint: str,
    model_name: str,
    api_key: str,
    mcp_servers: List[str] | None = None
):
    """Start a new Temporal workflow session."""
    # Start workflow
    # client = await get_temporal_client()
    # handle = await client.start_workflow(
    #     AgenticChatWorkflow.run,
    #     args=[session_id, model_endpoint, model_name, api_key, mcp_servers],
    #     id=f'agentic-chat-{session_id}',
    #     task_queue='agentic-chat'
    # )

    return {
        'session_id': 'session-123',
        'status': 'started'
    }

@app.post('/chat/agentic/session/{session_id}/message')
async def send_message(session_id: str, message: str, user_id: str):
    """Send a message to an active session."""
    # Get workflow handle
    # client = await get_temporal_client()
    # handle = client.get_workflow_handle(f'agentic-chat-{session_id}')
    # await handle.signal('process_message', user_id, message)

    return {'status': 'queued'}

@app.get('/chat/agentic/session/{session_id}/history')
async def get_history(session_id: str):
    """Get conversation history for a session."""
    # Query workflow
    # client = await get_temporal_client()
    # handle = client.get_workflow_handle(f'agentic-chat-{session_id}')
    # history = await handle.query('get_history')

    return {'history': []}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)
```

---

## 10. Best Practices & Common Pitfalls

### ✅ Best Practices

1. **Reuse Agent Instances**
   - Create agents once at startup
   - Use same agent for all sessions
   - Pass session-specific data via `deps` and `message_history`

2. **Use Dependencies for State**
   - Database connections
   - HTTP clients
   - User context
   - Configuration

3. **Set Appropriate max_steps**
   - Default is often too high
   - Start with 5-10 steps
   - Monitor and adjust based on usage

4. **Use Temperature 0 for Consistency**
   - When determinism is important
   - For evaluations and testing
   - For structured output extraction

5. **Implement Output Validators**
   - Validate safety/compliance
   - Check business rules
   - Use `ModelRetry` to request fixes

6. **Tool Prefixes for MCP Servers**
   - Always use prefixes when multiple servers
   - Prevents naming conflicts
   - Makes logs clearer

7. **Handle Message History Carefully**
   - Use `result.new_messages()` for continuation
   - Store serialized history: `result.all_messages_json()`
   - Implement history pruning for long conversations

8. **Streaming for Better UX**
   - Use `run_stream()` for real-time feedback
   - Show tool calls as they happen
   - Better perceived performance

9. **Comprehensive Error Handling**
   - Catch `UnexpectedModelBehavior`
   - Use `capture_run_messages()` for debugging
   - Log all errors with context

10. **Monitor Usage**
    - Track `result.usage()` for each run
    - Set `usage_limits` to prevent runaway costs
    - Implement rate limiting per user

### ❌ Common Pitfalls

1. **Not Passing Message History**
   ```python
   # ❌ BAD: No context between runs
   result1 = agent.run_sync('Who is Einstein?')
   result2 = agent.run_sync('When was he born?')  # Model has no context!

   # ✅ GOOD: Pass history
   result1 = agent.run_sync('Who is Einstein?')
   result2 = agent.run_sync('When was he born?',
                            message_history=result1.new_messages())
   ```

2. **Creating New Agent Per Request**
   ```python
   # ❌ BAD: Creates new connections every time
   @app.post('/chat')
   async def chat(message: str):
       agent = Agent('openai:gpt-4')  # DON'T DO THIS
       return await agent.run(message)

   # ✅ GOOD: Reuse agent
   AGENT = Agent('openai:gpt-4')  # Create once

   @app.post('/chat')
   async def chat(message: str):
       return await AGENT.run(message)
   ```

3. **Forgetting Dependencies in Deps Type**
   ```python
   # ❌ BAD: Type doesn't match actual deps
   agent = Agent('openai:gpt-4', deps_type=str)

   @agent.tool
   async def my_tool(ctx: RunContext[MyDeps]) -> str:  # Wrong type!
       return ctx.deps.database.query()

   # ✅ GOOD: Matching types
   agent = Agent('openai:gpt-4', deps_type=MyDeps)

   @agent.tool
   async def my_tool(ctx: RunContext[MyDeps]) -> str:
       return ctx.deps.database.query()
   ```

4. **Not Handling Tool Errors**
   ```python
   # ❌ BAD: Unhandled errors crash the agent
   @agent.tool
   async def fetch_data(url: str) -> str:
       response = await httpx.get(url)  # May fail
       return response.text

   # ✅ GOOD: Handle errors with ModelRetry
   @agent.tool(retries=3)
   async def fetch_data(url: str) -> str:
       try:
           response = await httpx.get(url)
           response.raise_for_status()
           return response.text
       except httpx.HTTPError as e:
           raise ModelRetry(f'Failed to fetch {url}: {e}')
   ```

5. **Infinite Loops with max_steps**
   ```python
   # ❌ BAD: No limit, can run forever
   agent = Agent('openai:gpt-4')  # Default max_steps may be high

   # ✅ GOOD: Set reasonable limit
   agent = Agent(
       'openai:gpt-4',
       settings=ModelSettings(max_steps=10)  # Explicit limit
   )
   ```

6. **Not Closing HTTP Clients**
   ```python
   # ❌ BAD: Leaks connections
   async def handle_request():
       deps = AgentDeps(http_client=httpx.AsyncClient())
       result = await agent.run('message', deps=deps)
       return result  # Client not closed!

   # ✅ GOOD: Use context manager
   async def handle_request():
       async with httpx.AsyncClient() as client:
           deps = AgentDeps(http_client=client)
           result = await agent.run('message', deps=deps)
           return result
   ```

7. **Mutating Shared Dependencies**
   ```python
   # ❌ BAD: Shared deps mutated across requests
   global_deps = MyDeps(...)

   @app.post('/chat')
   async def chat(message: str):
       result = await agent.run(message, deps=global_deps)
       # global_deps may have been modified!

   # ✅ GOOD: Create fresh deps per request
   @app.post('/chat')
   async def chat(message: str):
       deps = MyDeps(...)  # Fresh instance
       result = await agent.run(message, deps=deps)
   ```

8. **Not Using Tool Prefixes with Multiple MCP Servers**
   ```python
   # ❌ BAD: Tool name conflicts
   server1 = MCPServerSSE('http://server1')
   server2 = MCPServerSSE('http://server2')
   agent = Agent('openai:gpt-4', toolsets=[server1, server2])
   # If both have 'get_data' tool, conflict!

   # ✅ GOOD: Use prefixes
   server1 = MCPServerSSE('http://server1', tool_prefix='s1')
   server2 = MCPServerSSE('http://server2', tool_prefix='s2')
   agent = Agent('openai:gpt-4', toolsets=[server1, server2])
   # Tools: 's1_get_data', 's2_get_data'
   ```

9. **Expecting System Prompt in Message History**
   ```python
   # ❌ BAD: System prompt missing when passing history
   result1 = agent.run_sync('Message 1')
   # System prompt included automatically

   result2 = agent.run_sync(
       'Message 2',
       message_history=result1.new_messages()
   )
   # System prompt NOT re-added (assumes it's in history)

   # ✅ GOOD: Use all_messages() if you need complete history
   result2 = agent.run_sync(
       'Message 2',
       message_history=result1.all_messages()  # Includes system prompt
   )
   ```

10. **Not Monitoring Usage**
    ```python
    # ❌ BAD: No tracking of costs
    result = await agent.run('Complex task with many tool calls')
    return result.output

    # ✅ GOOD: Monitor and log usage
    result = await agent.run('Complex task')
    usage = result.usage()
    logger.info(
        f'Request tokens: {usage.request_tokens}, '
        f'Response tokens: {usage.response_tokens}, '
        f'Total requests: {usage.requests}'
    )
    return result.output
    ```

### Performance Tips

1. **Connection Pooling**: Reuse HTTP clients and database connections
2. **Async All The Way**: Don't block with `run_sync()` in async contexts
3. **Batch Where Possible**: Process multiple independent tasks concurrently
4. **Limit History Length**: Prune old messages to reduce token usage
5. **Use Caching**: Cache expensive tool results when appropriate
6. **Set Timeouts**: Always set request timeouts to prevent hangs
7. **Monitor Token Usage**: Track and optimize prompts to reduce costs

### Security Considerations

1. **Validate User Input**: Always validate/sanitize user messages
2. **Sandbox Tools**: Limit tool access to necessary operations only
3. **Rate Limiting**: Implement per-user rate limits
4. **Output Filtering**: Use validators to check for sensitive data leaks
5. **Secure Dependencies**: Never pass secrets in deps that could be logged
6. **MCP Server Trust**: Only connect to trusted MCP servers
7. **Audit Logging**: Log all agent interactions for security review

---

## Summary

Pydantic AI provides a robust framework for building agentic applications with:

- **Model Flexibility**: Support for any OpenAI-compatible endpoint
- **MCP Integration**: Seamless tool calling with MCP servers
- **Type Safety**: Full Pydantic v2 type checking and validation
- **Session Management**: Reusable agents with message history
- **Error Handling**: Built-in retry mechanisms and validation
- **Async First**: Native async/await support throughout
- **Production Ready**: FastAPI integration and streaming support

For LiteLLM's agentic routes running in Temporal workflows, the key patterns are:
1. Create agent once with custom model endpoint and MCP servers
2. Reuse agent across all sessions
3. Pass session-specific data via `deps` and `message_history`
4. Store message history in Temporal workflow state
5. Use signals for new messages, queries for history
6. Implement proper error handling and retry logic
7. Monitor usage and set appropriate limits

This architecture enables long-running, stateful agentic conversations with full tool integration and enterprise-grade reliability.
