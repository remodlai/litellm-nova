# Task-Based Routing for Nova Embeddings

Task-based routing enables automatic routing to task-specific model adapters based on the `task` parameter in requests.

## Setup Steps

### 1. Enable Tag Filtering

In `proxy_server_config.yaml` (or via UI settings):

```yaml
router_settings:
  enable_tag_filtering: True
```

### 2. Enable Nova Task Routing Hook

```yaml
litellm_settings:
  callbacks: ["nova_task_router"]
  drop_params: True
```

### 3. Add Task-Specific Deployments (Via UI)

For each task adapter, add a model with:

**Model Name (Public):** `nova-embeddings-v1` (SAME for all deployments)

**LiteLLM Params (JSON input):**
```json
{
  "model": "nova-embeddings-v1-retrieval",
  "api_base": "https://your-nova-endpoint/v1",
  "api_key": "your-key",
  "custom_llm_provider": "remodlai",
  "tags": ["retrieval", "retrieval.query", "retrieval.passage"]
}
```

**Repeat for each adapter:**

**Text-Matching:**
```json
{
  "model": "nova-embeddings-v1-text-matching",
  "api_base": "https://your-nova-endpoint/v1",
  "api_key": "your-key",
  "custom_llm_provider": "remodlai",
  "tags": ["text-matching"]
}
```

**Code:**
```json
{
  "model": "nova-embeddings-v1-code",
  "api_base": "https://your-nova-endpoint/v1",
  "api_key": "your-key",
  "custom_llm_provider": "remodlai",
  "tags": ["code", "code.query", "code.passage"]
}
```

## Important Rules

### DO NOT Add Base Model

❌ **Do NOT add a deployment for the base model** (`nova-embeddings-v1`) without tags or with "default" tag.

If you add it, requests will route to the base model instead of task-specific adapters.

### Add Tags in litellm_params JSON

✅ **Correct:** Add tags in the litellm_params JSON field
```json
{"tags": ["retrieval"]}
```

❌ **Incorrect:** Using the tag management UI causes validation errors requiring manual database cleanup.

## How It Works

**Client Request:**
```json
{
  "model": "nova-embeddings-v1",
  "task": "retrieval.query",
  "input": ["search query"]
}
```

**Routing Flow:**
1. Hook converts `task: "retrieval.query"` → `metadata.tags: ["retrieval.query"]`
2. Router finds all deployments with `model_name: "nova-embeddings-v1"`
3. Filters to deployments with matching tags (ANY overlap)
4. Deployment with tags `["retrieval", "retrieval.query", "retrieval.passage"]` matches
5. Routes to that deployment's `api_base` with model `"nova-embeddings-v1-retrieval"`
6. Nova activates retrieval LoRA adapter

## Scaling with Load Balancing

Task-based routing combines with load balancing strategies:

**Example: 10 retrieval instances**

```json
// Deployment 1
{"model": "nova-embeddings-v1-retrieval", "api_base": "https://pod1/v1", "tags": ["retrieval"]}

// Deployment 2
{"model": "nova-embeddings-v1-retrieval", "api_base": "https://pod2/v1", "tags": ["retrieval"]}

// ... 8 more retrieval deployments
```

**Routing:**
1. Tag filter: Down to 10 retrieval deployments
2. Load balancing strategy (least-busy/simple-shuffle): Pick from pool
3. Scales horizontally per task type

**Configuration:**
```yaml
router_settings:
  enable_tag_filtering: True
  routing_strategy: least-busy  # or simple-shuffle, latency-based, etc.
```

## Verification

### Check Models Loaded
```bash
curl http://localhost:4000/v1/models -H "Authorization: Bearer sk-1234"
```

Should show `nova-embeddings-v1` (and task-specific variants if added separately).

### Test Task Routing

**Retrieval request:**
```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval.query",
    "input": ["test query"]
  }'
```

**Check logs with verbose enabled:**
```
NovaTaskRoutingHook: Converting task 'retrieval.query' to tag
Updated metadata tags: ['retrieval.query']
litellm.aembedding(model=nova-embeddings-v1-retrieval) 200 OK
```

### Test Different Tasks

**Text-matching:**
```json
{"model": "nova-embeddings-v1", "task": "text-matching", "input": [...]}
```

**Code:**
```json
{"model": "nova-embeddings-v1", "task": "code.query", "input": [...]}
```

Each should route to the corresponding adapter.

## Multi-Backend Deployment

Task routing works across different Nova instances:

```json
// Retrieval on RunPod
{"model": "nova-embeddings-v1-retrieval", "api_base": "https://runpod.net/v1", "tags": ["retrieval"]}

// Text-matching on Modal
{"model": "nova-embeddings-v1-text-matching", "api_base": "https://modal.com/v1", "tags": ["text-matching"]}

// Code on Lambda Labs
{"model": "nova-embeddings-v1-code", "api_base": "https://lambda.ai/v1", "tags": ["code"]}
```

The gateway handles routing regardless of where adapters are physically deployed.

## Troubleshooting

**Problem: Requests go to wrong adapter**
- Check `enable_tag_filtering: True` is set
- Verify tags include the exact task value
- Check hook is in callbacks list

**Problem: "No deployments with tag" error**
- Verify at least one deployment has matching tag
- Check tags are in litellm_params JSON, not via UI
- Ensure task parameter is in request

**Problem: Base64 response too large**
- Use `encoding_format: "float"` instead of "base64" for smaller responses
- Or use `return_multivector: false` for pooled embeddings
