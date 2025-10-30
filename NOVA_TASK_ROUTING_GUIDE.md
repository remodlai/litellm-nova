# Nova Embeddings V1 - Task-Based Routing Guide

## Overview

Nova Embeddings V1 uses **task-specific LoRA adapters** that must be activated based on the `task` parameter in requests. This guide explains how LiteLLM routes requests to the correct adapter using the existing tag-based routing system.

## Architecture

```
User Request                   LiteLLM Proxy              Nova Server
────────────                   ─────────────              ────────────
POST /v1/embeddings            
{                              
  "model": "nova-embeddings-v1"
  "task": "retrieval.passage" ──→ Hook converts to     ──→ Routes to
  "input": [...]                   tags: ["retrieval.      nova-embeddings-retrieval
}                                       passage"]          (activates retrieval LoRA)
```

## How It Works

### 1. Pre-Call Hook (`NovaTaskRoutingHook`)

Located at: `litellm/proxy/hooks/nova_task_routing.py`

**What it does:**
- Intercepts embedding requests before routing
- Extracts `task` parameter from request body
- Converts it to `metadata.tags`
- Passes to existing tag router

**Example transformation:**
```python
# Before hook
{
  "model": "nova-embeddings-v1",
  "task": "retrieval.passage",
  "input": [...]
}

# After hook
{
  "model": "nova-embeddings-v1",
  "task": "retrieval.passage",  # Preserved
  "metadata": {"tags": ["retrieval.passage"]},  # Added for routing
  "input": [...]
}
```

### 2. Tag Router (Existing)

Located at: `litellm/router_strategy/tag_based_routing.py`

**What it does:**
- Matches `tags` in request metadata to `tags` in deployment config
- Selects deployments where request tags match deployment tags
- Returns matching deployments to router

### 3. Model Selection

Router picks from matched deployments based on `routing_strategy` (simple-shuffle, least-busy, etc.)

## Configuration

### proxy_server_config.yaml

```yaml
model_list:
  # Retrieval adapter - handles retrieval, retrieval.query, retrieval.passage
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-retrieval
      api_base: os.environ/REMODLAI_API_BASE
      api_key: os.environ/REMODLAI_API_KEY
      tags: ["retrieval", "retrieval.query", "retrieval.passage"]
    model_info:
      mode: embedding
      id: nova-embeddings-retrieval

  # Text-matching adapter
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-text-matching
      api_base: os.environ/REMODLAI_API_BASE
      api_key: os.environ/REMODLAI_API_KEY
      tags: ["text-matching"]
    model_info:
      mode: embedding
      id: nova-embeddings-text-matching

  # Code adapter - handles code, code.query, code.passage
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-code
      api_base: os.environ/REMODLAI_API_BASE
      api_key: os.environ/REMODLAI_API_KEY
      tags: ["code", "code.query", "code.passage"]
    model_info:
      mode: embedding
      id: nova-embeddings-code

litellm_settings:
  callbacks: litellm.proxy.hooks.nova_task_routing.nova_task_router  # ← Enable hook
  drop_params: True

router_settings:
  enable_tag_filtering: True  # ← Enable tag routing
  routing_strategy: simple-shuffle

general_settings:
  master_key: sk-1234
```

## Usage Examples

### Basic Retrieval

```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval",
    "input": ["search query", "document text"]
  }'
```

**Result:** Routed to `nova-embeddings-retrieval` (retrieval LoRA activated)

### Query vs Passage

```bash
# Query (optimized for search)
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval.query",
    "instructions": "Focus on legal precedents",
    "input": [{"text": "trademark dilution doctrine"}]
  }'

# Passage (optimized for indexing)
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval.passage",
    "input": [{"text": "Under the Lanham Act..."}]
  }'
```

**Result:** Both routed to `nova-embeddings-retrieval` (same adapter, different prompts)

### Text Matching

```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "text-matching",
    "input": ["Text A", "Text B"]
  }'
```

**Result:** Routed to `nova-embeddings-text-matching`

### Code Search

```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "code.query",
    "instructions": "Focus on function purpose, ignore variable names",
    "input": [{"text": "function to parse JSON"}]
  }'
```

**Result:** Routed to `nova-embeddings-code`

### Multimodal with Instructions

```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval.passage",
    "return_multivector": true,
    "instructions": "Analyze document layout on 28x28 grid. Extract concepts and relationships.",
    "input": [{
      "image": "https://media.eagereyes.org/wp-content/uploads/2016/05/pie-package-teaser.png"
    }, {
      "text": "some text"
    }]
  }'
```

**Result:** Routed to `nova-embeddings-retrieval`, passes all params to Nova server

## Task → Adapter Mapping

| Request Task | Deployment Tags | Backend Model | LoRA Activated |
|--------------|----------------|---------------|----------------|
| `retrieval` | `["retrieval", "retrieval.query", "retrieval.passage"]` | `nova-embeddings-retrieval` | retrieval |
| `retrieval.query` | Same | `nova-embeddings-retrieval` | retrieval |
| `retrieval.passage` | Same | `nova-embeddings-retrieval` | retrieval |
| `text-matching` | `["text-matching"]` | `nova-embeddings-text-matching` | text-matching |
| `code` | `["code", "code.query", "code.passage"]` | `nova-embeddings-code` | code |
| `code.query` | Same | `nova-embeddings-code` | code |
| `code.passage` | Same | `nova-embeddings-code` | code |

## Verification

### Check Routing is Working

Look for the `x-remodl-model-id` header in responses:

```bash
curl -i http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval",
    "input": ["test"]
  }'
```

**Expected header:**
```
x-remodl-model-id: nova-embeddings-retrieval
```

### Enable Debug Logging

To see routing decisions:

```yaml
litellm_settings:
  set_verbose: True  # ← Enable debug logs
  callbacks: litellm.proxy.hooks.nova_task_routing.nova_task_router
```

You'll see logs like:
```
NovaTaskRoutingHook: Converting task 'retrieval.passage' to tag for model 'nova-embeddings-v1'
get_deployments_for_tag routing: router_keys: ['retrieval.passage']
adding deployment with tags: ['retrieval', 'retrieval.query', 'retrieval.passage']
```

## Multiple Nova Servers

You can configure different Nova servers for different adapters:

```yaml
model_list:
  # Server 1: Retrieval on GPU 0
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-retrieval
      api_base: https://nova-server-1.com  # ← Server 1
      tags: ["retrieval", "retrieval.query", "retrieval.passage"]

  # Server 2: Code on GPU 1
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-code
      api_base: https://nova-server-2.com  # ← Server 2
      tags: ["code", "code.query", "code.passage"]
```

## Fallback / Default Routing

Add a default deployment for requests without task:

```yaml
model_list:
  # ... task-specific deployments ...
  
  # Default: route untagged requests to retrieval
  - model_name: nova-embeddings-v1
    litellm_params:
      model: remodlai/nova-embeddings-retrieval
      api_base: os.environ/REMODLAI_API_BASE
      tags: ["default"]  # ← Catches requests without task
```

## Troubleshooting

### Error: "No deployments found with tag routing"

**Cause:** No deployment matches the task tag

**Solution:** Verify:
1. `enable_tag_filtering: True` in router_settings
2. Task value matches a deployment tag
3. Deployment has `tags` array in litellm_params

### Hook Not Running

**Cause:** Callback not loaded

**Solution:** Check `litellm_settings.callbacks` includes the hook path

### Task Not Converted to Tag

**Cause:** Model name doesn't contain "nova-embeddings"

**Solution:** Ensure model_name or litellm_params.model includes "nova-embeddings"

## Summary

✅ **No router modifications needed** - uses existing tag routing  
✅ **Simple hook** converts `task` → `tags`  
✅ **Flexible deployment** - separate servers, GPUs, or single endpoint  
✅ **Transparent to users** - they just set `task` parameter  
✅ **Standard LiteLLM features** - fallbacks, load balancing, retries all work  

The Nova task routing seamlessly integrates with LiteLLM's existing infrastructure!

