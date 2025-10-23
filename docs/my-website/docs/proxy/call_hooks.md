import Image from '@theme/IdealImage';

# Modify / Reject Incoming Requests

- Modify data before making llm api calls on proxy
- Reject data before making llm api calls / before returning the response 
- Enforce 'user' param for all openai endpoint calls

:::tip
**Understanding Callback Hooks?** Check out our [Callback Management Guide](../observability/callback_management.md) to understand the differences between proxy-specific hooks like `async_pre_call_hook` and general logging hooks like `async_log_success_event`.
:::

See a complete example with our [parallel request rate limiter](https://github.com/BerriAI/litellm/blob/main/litellm/proxy/hooks/parallel_request_limiter.py)

## Quick Start

1. In your Custom Handler add a new `async_pre_call_hook` function

This function is called just before a litellm completion call is made, and allows you to modify the data going into the litellm call [**See Code**](https://github.com/BerriAI/litellm/blob/589a6ca863000ba8e92c897ba0f776796e7a5904/litellm/proxy/proxy_server.py#L1000)

```python
from litellm.integrations.custom_logger import CustomLogger
import litellm
from litellm.proxy.proxy_server import UserAPIKeyAuth, DualCache
from litellm.types.utils import ModelResponseStream
from typing import Any, AsyncGenerator, Optional, Literal

# This file includes the custom callbacks for LiteLLM Proxy
# Once defined, these can be passed in proxy_config.yaml
class MyCustomHandler(CustomLogger): # https://docs.litellm.ai/docs/observability/custom_callback#callback-class
    # Class variables or attributes
    def __init__(self):
        pass

    #### CALL HOOKS - proxy only #### 

    async def async_pre_call_hook(self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: Literal[
            "completion",
            "text_completion",
            "embeddings",
            "image_generation",
            "moderation",
            "audio_transcription",
        ]): 
        data["model"] = "my-new-model"
        return data 

    async def async_post_call_failure_hook(
        self, 
        request_data: dict,
        original_exception: Exception, 
        user_api_key_dict: UserAPIKeyAuth,
        traceback_str: Optional[str] = None,
    ):
        pass

    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        response,
    ):
        pass

    async def async_moderation_hook( # call made in parallel to llm api call
        self,
        data: dict,
        user_api_key_dict: UserAPIKeyAuth,
        call_type: Literal["completion", "embeddings", "image_generation", "moderation", "audio_transcription"],
    ):
        pass

    async def async_post_call_streaming_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        response: str,
    ):
        pass

    async def async_post_call_streaming_iterator_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        response: Any,
        request_data: dict,
    ) -> AsyncGenerator[ModelResponseStream, None]:
        """
        Passes the entire stream to the guardrail

        This is useful for plugins that need to see the entire stream.
        """
        async for item in response:
            yield item

proxy_handler_instance = MyCustomHandler()
```

2. Add this file to your proxy config

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo

litellm_settings:
  callbacks: custom_callbacks.proxy_handler_instance # sets litellm.callbacks = [proxy_handler_instance]
```

3. Start the server + test the request

```shell
$ litellm /path/to/config.yaml
```
```shell
curl --location 'http://0.0.0.0:4000/chat/completions' \
    --data ' {
    "model": "gpt-3.5-turbo",
    "messages": [
        {
        "role": "user",
        "content": "good morning good sir"
        }
    ],
    "user": "ishaan-app",
    "temperature": 0.2
    }'
```


## [BETA] *NEW* async_moderation_hook 

Run a moderation check in parallel to the actual LLM API call. 

In your Custom Handler add a new `async_moderation_hook` function

- This is currently only supported for `/chat/completion` calls. 
- This function runs in parallel to the actual LLM API call. 
- If your `async_moderation_hook` raises an Exception, we will return that to the user. 


:::info

We might need to update the function schema in the future, to support multiple endpoints (e.g. accept a call_type). Please keep that in mind, while trying this feature

:::

See a complete example with our [Llama Guard content moderation hook](https://github.com/BerriAI/litellm/blob/main/enterprise/enterprise_hooks/llm_guard.py)

```python
from litellm.integrations.custom_logger import CustomLogger
import litellm
from fastapi import HTTPException

# This file includes the custom callbacks for LiteLLM Proxy
# Once defined, these can be passed in proxy_config.yaml
class MyCustomHandler(CustomLogger): # https://docs.litellm.ai/docs/observability/custom_callback#callback-class
    # Class variables or attributes
    def __init__(self):
        pass

    #### ASYNC #### 
    
    async def async_log_pre_api_call(self, model, messages, kwargs):
        pass

    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        pass

    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        pass

    #### CALL HOOKS - proxy only #### 

    async def async_pre_call_hook(self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: Literal["completion", "embeddings"]):
        data["model"] = "my-new-model"
        return data 
    
    async def async_moderation_hook( ### 👈 KEY CHANGE ###
        self,
        data: dict,
    ):
        messages = data["messages"]
        print(messages)
        if messages[0]["content"] == "hello world": 
            raise HTTPException(
                    status_code=400, detail={"error": "Violated content safety policy"}
                )

proxy_handler_instance = MyCustomHandler()
```


2. Add this file to your proxy config

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo

litellm_settings:
  callbacks: custom_callbacks.proxy_handler_instance # sets litellm.callbacks = [proxy_handler_instance]
```

3. Start the server + test the request

```shell
$ litellm /path/to/config.yaml
```
```shell
curl --location 'http://0.0.0.0:4000/chat/completions' \
    --data ' {
    "model": "gpt-3.5-turbo",
    "messages": [
        {
        "role": "user",
        "content": "Hello world"
        }
    ],
    }'
```

## Advanced - Enforce 'user' param 

Set `enforce_user_param` to true, to require all calls to the openai endpoints to have the 'user' param. 

[**See Code**](https://github.com/BerriAI/litellm/blob/4777921a31c4c70e4d87b927cb233b6a09cd8b51/litellm/proxy/auth/auth_checks.py#L72)

```yaml
general_settings:
  enforce_user_param: True
```

**Result**

<Image img={require('../../img/end_user_enforcement.png')}/>

## Advanced - Return rejected message as response 

For chat completions and text completion calls, you can return a rejected message as a user response. 

Do this by returning a string. LiteLLM takes care of returning the response in the correct format depending on the endpoint and if it's streaming/non-streaming.

For non-chat/text completion endpoints, this response is returned as a 400 status code exception. 


### 1. Create Custom Handler 

```python
from litellm.integrations.custom_logger import CustomLogger
import litellm
from litellm.utils import get_formatted_prompt

# This file includes the custom callbacks for LiteLLM Proxy
# Once defined, these can be passed in proxy_config.yaml
class MyCustomHandler(CustomLogger):
    def __init__(self):
        pass

    #### CALL HOOKS - proxy only #### 

    async def async_pre_call_hook(self, user_api_key_dict: UserAPIKeyAuth, cache: DualCache, data: dict, call_type: Literal[
            "completion",
            "text_completion",
            "embeddings",
            "image_generation",
            "moderation",
            "audio_transcription",
        ]) -> Optional[dict, str, Exception]: 
        formatted_prompt = get_formatted_prompt(data=data, call_type=call_type)

        if "Hello world" in formatted_prompt:
            return "This is an invalid response"

        return data 

proxy_handler_instance = MyCustomHandler()
```

### 2. Update config.yaml 

```yaml
model_list:
  - model_name: gpt-3.5-turbo
    litellm_params:
      model: gpt-3.5-turbo

litellm_settings:
  callbacks: custom_callbacks.proxy_handler_instance # sets litellm.callbacks = [proxy_handler_instance]
```


### 3. Test it!

```shell
$ litellm /path/to/config.yaml
```
```shell
curl --location 'http://0.0.0.0:4000/chat/completions' \
    --data ' {
    "model": "gpt-3.5-turbo",
    "messages": [
        {
        "role": "user",
        "content": "Hello world"
        }
    ],
    }'
```

**Expected Response**

```
{
    "id": "chatcmpl-d00bbede-2d90-4618-bf7b-11a1c23cf360",
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "message": {
                "content": "This is an invalid response.", # 👈 REJECTED RESPONSE
                "role": "assistant"
            }
        }
    ],
    "created": 1716234198,
    "model": null,
    "object": "chat.completion",
    "system_fingerprint": null,
    "usage": {}
}
```

## Creating Built-in Hooks

The examples above show external callback files. For hooks that are part of the LiteLLM codebase (like rate limiters or task routing), follow this pattern:

### Step 1: Create Hook File

**Location:** `litellm/proxy/hooks/your_hook_name.py`

**Example:** Nova Task Routing Hook

```python
"""
Nova Embeddings Task-Based Routing Hook

Converts Nova's 'task' parameter to LiteLLM's tag-based routing.
"""

from typing import TYPE_CHECKING, Any, Literal, Optional

from litellm._logging import verbose_logger
from litellm.integrations.custom_logger import CustomLogger

if TYPE_CHECKING:
    from litellm.proxy.proxy_server import DualCache, UserAPIKeyAuth
else:
    DualCache = Any
    UserAPIKeyAuth = Any


class NovaTaskRoutingHook(CustomLogger):
    """
    Converts Nova Embeddings 'task' parameter to tag-based routing.
    """

    def __init__(self):
        super().__init__()
        verbose_logger.debug("NovaTaskRoutingHook initialized")

    async def async_pre_call_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        cache: DualCache,
        data: dict,
        call_type: Literal[
            "completion",
            "text_completion",
            "embeddings",
            "image_generation",
            "moderation",
            "audio_transcription",
        ],
    ):
        # Only process embedding requests
        if call_type != "embeddings":
            return data
        
        # Only process Nova embedding models
        if "nova-embeddings" not in data.get("model", ""):
            return data
        
        # Extract the task parameter
        task = data.get("task")
        
        if not task:
            return data
        
        # Initialize metadata if not present
        if "metadata" not in data:
            data["metadata"] = {}
        
        if "tags" not in data["metadata"]:
            data["metadata"]["tags"] = []
        
        # Add task to tags
        if task not in data["metadata"]["tags"]:
            data["metadata"]["tags"].append(task)
        
        return data


# Create singleton instance
nova_task_router = NovaTaskRoutingHook()
```

### Step 2: Register the Hook

#### 2a. Add to Type Literal

**File:** `litellm/__init__.py` (line ~117)

```python
_custom_logger_compatible_callbacks_literal = Literal[
    "lago",
    "openmeter",
    "dynamic_rate_limiter",
    "nova_task_router",  # ← Add your hook name
    "langsmith",
    # ...
]
```

#### 2b. Register in Custom Logger Registry

**File:** `litellm/litellm_core_utils/custom_logger_registry.py`

**Import your hook (top of file):**
```python
from litellm.proxy.hooks.nova_task_routing import NovaTaskRoutingHook
```

**Add to registry (line ~94):**
```python
CALLBACK_CLASS_STR_TO_CLASS_TYPE = {
    "lago": LagoLogger,
    "dynamic_rate_limiter": _PROXY_DynamicRateLimitHandler,
    "nova_task_router": NovaTaskRoutingHook,  # ← Add mapping
    # ...
}
```

#### 2c. Export from Hooks Module

**File:** `litellm/proxy/hooks/__init__.py`

```python
from .nova_task_routing import NovaTaskRoutingHook, nova_task_router

PROXY_HOOKS = {
    "nova_task_router": NovaTaskRoutingHook,
}

__all__ = [
    "NovaTaskRoutingHook",
    "nova_task_router",
]
```

### Step 3: Use in Config

**Method 1: String name (Recommended - allows multiple callbacks)**

```yaml
litellm_settings:
  callbacks: ["nova_task_router", "langfuse", "prometheus"]
```

**Method 2: Direct import (Single callback only)**

```yaml
litellm_settings:
  callbacks: litellm.proxy.hooks.nova_task_routing.nova_task_router
```

### Step 4: Test

```bash
# Enable verbose logging
litellm --config proxy_server_config.yaml --detailed_debug

# Make request
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "remodlai/nova-embeddings-v1",
    "task": "retrieval.query",
    "input": ["test query"]
  }'

# Check logs for:
# - "NovaTaskRoutingHook initialized"
# - "NovaTaskRoutingHook: Converting task 'retrieval.query' to tag"
# - "Updated metadata tags: ['retrieval.query']"
```

## Hook Execution Flow

Understanding when your hook runs (from `litellm/proxy/proxy_server.py`):

```
/v1/embeddings endpoint:
├─ Line 4674: Request body parsed
├─ Line 4736: async_pre_call_hook() ← YOUR HOOK RUNS HERE
│   └─ Modifies data (add tags, change model, etc.)
├─ Line 4750: route_request()
│   └─ Router uses modified data to select deployment
└─ Line 4756: LLM API call made
```

**Key Point:** Hook runs BEFORE routing, so modifications affect deployment selection.

## Real-World Example: Nova Task Routing

**Use Case:** Route embedding requests to task-specific LoRA adapters based on `task` parameter.

**Problem:** Clients send `task: "retrieval.query"`, but LiteLLM routes by model name and tags, not custom params.

**Solution:** Hook converts `task` → `metadata.tags`, enabling tag-based routing.

**Config:**
```yaml
# Enable tag filtering
router_settings:
  enable_tag_filtering: True

# Enable hook
litellm_settings:
  callbacks: ["nova_task_router"]
```

**Deployments (in DB):**
```
Model 1: nova-embeddings-v1
  Backend: nova-embeddings-v1-retrieval
  Tags: ["retrieval", "retrieval.query", "retrieval.passage"]

Model 2: nova-embeddings-v1
  Backend: nova-embeddings-v1-text-matching
  Tags: ["text-matching"]

Model 3: nova-embeddings-v1
  Backend: nova-embeddings-v1-code  
  Tags: ["code", "code.query", "code.passage"]
```

**Request flow:**
1. Client: `{"model": "nova-embeddings-v1", "task": "retrieval.query"}`
2. Hook: Adds `metadata.tags: ["retrieval.query"]`
3. Router: Matches Model 1 (has "retrieval.query" in tags)
4. Calls: `nova-embeddings-v1-retrieval` backend
5. Nova: Activates retrieval LoRA adapter

**Code Location:** `litellm/proxy/hooks/nova_task_routing.py`

## Code Reference Locations

| What | File | Line(s) |
|------|------|---------|
| Hook class | `litellm/proxy/hooks/nova_task_routing.py` | 43-127 |
| Literal type | `litellm/__init__.py` | 117-158 |
| Registry import | `litellm/litellm_core_utils/custom_logger_registry.py` | 53 |
| Registry mapping | `litellm/litellm_core_utils/custom_logger_registry.py` | 94 |
| Hook export | `litellm/proxy/hooks/__init__.py` | 23, 62 |
| Pre-call execution | `litellm/proxy/proxy_server.py` | 4736 (embeddings), similar for other endpoints |
| Tag filtering | `litellm/router_strategy/tag_based_routing.py` | 39-120 |

## Debugging Tips

**1. Check hook is loaded:**
```bash
# Start proxy with verbose logging
LITELLM_LOG=DEBUG litellm --config config.yaml

# Should see:
# "NovaTaskRoutingHook initialized"
```

**2. Trace hook execution:**
Add verbose logging in your hook:
```python
verbose_logger.debug("Hook input: %s", data)
verbose_logger.debug("Hook output: %s", modified_data)
```

**3. Verify registration:**
```python
# In Python console
from litellm.litellm_core_utils.custom_logger_registry import CustomLoggerRegistry
print("nova_task_router" in CustomLoggerRegistry.CALLBACK_CLASS_STR_TO_CLASS_TYPE)
# Should print: True
```

**4. Test hook directly:**
```python
import asyncio
from litellm.proxy.hooks.nova_task_routing import NovaTaskRoutingHook

async def test():
    hook = NovaTaskRoutingHook()
    data = {"model": "nova-embeddings-v1", "task": "retrieval"}
    result = await hook.async_pre_call_hook(None, None, data, "embeddings")
    print(result)

asyncio.run(test())
```

## Common Patterns

### Pattern: Conditional Processing

```python
async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
    # Process only specific call types
    if call_type != "embeddings":
        return data
    
    # Process only specific models
    if not data.get("model", "").startswith("your-prefix/"):
        return data
    
    # Your logic here
    return data
```

### Pattern: Safe Metadata Modification

```python
async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
    # Safely initialize nested structures
    if "metadata" not in data:
        data["metadata"] = {}
    
    if "tags" not in data["metadata"]:
        data["metadata"]["tags"] = []
    
    # Add without duplicates
    new_tag = compute_tag(data)
    if new_tag not in data["metadata"]["tags"]:
        data["metadata"]["tags"].append(new_tag)
    
    return data
```

### Pattern: Parameter Transformation

```python
async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
    # Convert custom param to standard param
    if "custom_param" in data:
        custom_value = data.pop("custom_param")  # Remove from data
        data["standard_param"] = transform(custom_value)
    
    return data
```
