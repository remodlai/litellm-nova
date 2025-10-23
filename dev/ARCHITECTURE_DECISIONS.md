# Architecture Decisions for LiteLLM Nova Integration

## Decision 1: Use Tag-Based Routing for Nova Task Adapters

**Date:** 2025-10-22

### Context

Nova Embeddings V1 uses task-specific LoRA adapters (retrieval, text-matching, code) that are served as separate model endpoints. Users specify which adapter to use via the `task` parameter in their embedding requests.

### Problem

How do we route embedding requests to the correct Nova adapter endpoint based on the `task` parameter?

### Options Considered

1. **Create new task-based routing system**
   - Pros: Clean separation, task-specific logic
   - Cons: Duplicate code, new routing layer to maintain

2. **Extend tag routing to understand 'task' parameter**
   - Pros: Reuses proven routing system
   - Cons: Slight conceptual overload of "tags"

3. **Use async_pre_call_hook to convert task → tags** ✅ **CHOSEN**
   - Pros: Zero router changes, leverages existing tag system, clean separation
   - Cons: Adds a hook layer (minimal overhead)

### Decision

**Use `async_pre_call_hook` to convert `task` parameter to `metadata.tags`**

### Rationale

1. **No router modifications needed** - LiteLLM's tag routing already does exactly what we need
2. **Clean separation** - Nova-specific logic isolated in a hook, easy to test and maintain
3. **Flexible** - Works with any number of adapters, servers, or deployment configurations
4. **Standard patterns** - Uses LiteLLM's documented hook system
5. **Future-proof** - If task routing becomes common, we can move it to core

### Implementation

**Hook:** `litellm/proxy/hooks/nova_task_routing.py`
- Intercepts embedding requests
- Extracts `task` parameter
- Adds to `metadata.tags`
- Passes to existing tag router

**Config pattern:**
```yaml
model_list:
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-retrieval
      tags: ["retrieval", "retrieval.query", "retrieval.passage"]

litellm_settings:
  callbacks: litellm.proxy.hooks.nova_task_routing.nova_task_router

router_settings:
  enable_tag_filtering: True
```

### Trade-offs Accepted

- **Hook overhead**: ~0.1ms per request (negligible)
- **Tag system overloading**: Tags used for both user tags and task routing (acceptable - they're conceptually similar)

### Alternatives Rejected

- **Modify core router**: Would add complexity to core codebase for provider-specific feature
- **Separate routing layer**: Duplicate code and maintenance burden
- **Hard-coded task logic**: Not flexible enough for custom adapters

### Success Criteria

- [x] Works with existing tag router
- [x] Supports all Nova tasks (retrieval, text-matching, code, subtasks)
- [x] No performance degradation
- [x] Easy to configure
- [x] Test coverage for hook logic

---

## Decision 2: Nova as Model Provider (Not Fixed Model List)

**Date:** 2025-10-22

### Context

Lexiq Nova (like vLLM) is a model serving platform that can serve multiple different models, not just nova-embeddings-v1.

### Problem

Should the UI treat Lexiq Nova as:
- A provider with a fixed list of known models?
- A provider where users can specify any model name?

### Decision

**Treat Lexiq Nova as a model provider (like vLLM, Ollama, Azure)** ✅

Users can enter ANY model name in the UI text field:
- `nova-embeddings-v1`
- `nova-embeddings-retrieval`
- `llama-3.1-70b-instruct`
- Custom fine-tuned models
- etc.

### Rationale

1. **Flexibility** - Nova can serve any model
2. **Consistency** - Matches vLLM/Ollama pattern users already understand
3. **Future-proof** - New models don't require UI updates
4. **Accurate representation** - Nova IS a platform, not a single model

### Implementation

**UI Changes:**
- Added to provider dropdown
- Text input field (not dropdown) for model name
- Placeholder: "nova-embeddings-v1"
- Same pattern as vLLM, Ollama, Azure

**Files modified:**
- `ui/litellm-dashboard/src/components/provider_info_helpers.tsx`
- `ui/litellm-dashboard/src/components/add_model/litellm_model_name.tsx`
- `ui/litellm-dashboard/src/components/add_model/provider_specific_fields.tsx`

---

## Decision 3: Jina V4 Compatibility in Nova Implementation

**Date:** 2025-10-22

### Context

Nova Embeddings V1 is built on Jina Embeddings V4 architecture with added features.

### Decision

**Maintain 100% Jina V4 compatibility while adding Nova-specific features**

### Implementation

- Same base64 image handling as Jina
- Same response format (standard OpenAI `EmbeddingResponse`)
- Same `dimensions` parameter support
- Nova features (instructions, task, return_multivector) are additive

### Rationale

1. **Migration path** - Users can swap Jina V4 → Nova V1 with zero code changes
2. **Fallback** - If Nova-specific features not needed, works like Jina V4
3. **Ecosystem compatibility** - Works with existing Jina V4 tooling

### Code

```python
# This Jina V4 code...
litellm.embedding(model="jina_ai/jina-embeddings-v4", input=["text"], dimensions=512)

# ...works identically with Nova V1
litellm.embedding(model="remodlai/nova-embeddings-v1", input=["text"], dimensions=512)

# Plus you can add Nova features
litellm.embedding(
    model="remodlai/nova-embeddings-v1",
    input=["text"],
    dimensions=512,
    instructions="Focus on legal terminology",  # Nova-specific
    task="retrieval",  # Nova-specific
)
```
