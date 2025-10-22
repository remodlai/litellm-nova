# This describes the current project you are working on. It is a living document.


# Objective: Integrate Nova-embeddings-v1 properly for lexiq_nova and hosted_lexiq_nova providers
Correctly integrate the jinaai/jina-embeddings-v4 based model from Remodl AI called nova-embeddings-v1 into `litellm/llms/hosted_lexiq_nova` and `litellm/llms/lexiq_nova`, ensuring that the proper handing and integration is completed, respecting the unique functionality of this model.


## What is this model?

The nova-embeddings-v1 model is a SOTA multimodal instruction-tunable embeddings model that is able to return:

- **Single dense vector embeddings** (standard 2048 dimension, definable as low as 128 dimensions)
  - ONLY single vector is able to have dimensions defined (passed as `dimensions` request param)
- **Multi-vector embeddings** with 128 dimensions per token
- **Embeddings can be returned** either as standard float or base64 encoded
- **Task-specific activation** via the `task` request param, falling into 3 core tasks:
  - `retrieval`: for analysis of text and images. Supports 2 subtasks:
    - `retrieval.query`: optimizes embeddings for SEARCH
    - `retrieval.passage`: optimizes embeddings for storage and FUTURE SEARCH
    - **KEY NOTE**: the combination of `instructions` with the task.subtask enables highly specific performance.
  - `text-matching`: specialized comparison analysis between 2+ inputs
  - `code`: functionally similar to `retrieval` but with codebase-analysis optimizations

#### The TASK MUST ALIGN WITH THE SPECIFIC ACTIVATED LORA BEING SERVED FROM NOVA

**HOW THIS WORKS:**
When this model is launched in a LexIQ Nova server instance we also define the specific model paths, e.g `nova-embeddings-retrieval` (as an example) is in fact the lora-identifier to activate the retrieval task adapter. **The task param in the request must align to the proper route in litellm**. See #3 below for suggested solution.

- A single request can include both `image` and `text` inputs, as well as an optional `image_embeds` which are precomputed embeddings. These are passed as an array. No remapping or translation should occur.

## TO BE DELIVERED:

### 1. A complete review and comprehension of the nova-embeddings-v1 model

Located within the workspace at `/Users/brianbagdasarian/projects/worker-infinity-embedding/models/remodlai/nova-embeddings-v1`.

- Careful review of the README.md, Nova embeddings alters the original functionality of jina-embeddings-v4. We separated the original multi-task lora adapter into 3 standard task adapters.
- Careful review of `/Users/brianbagdasarian/projects/worker-infinity-embedding/models/remodlai/nova-embeddings-v1/modeling_nova_embeddings_v1.py`
- Reflection and follow up questions to the user as needed.

### 2. Review of the existing jina integration

Which may reference jina-embeddings-v3, but NOT jina-embeddings-v4. It is ~80%-90% similar to our needs.

### 3. Review tag-based routing in litellm

Review https://docs.litellm.ai/docs/proxy/tag_routing to understand tag-based routing in litellm.

**Suggested solution for managing routing to correct nova routes:** We modify the `tags` handling in litellm to also work with `task` when passed in a request AND the model string includes `nova-embeddings`




Example:
This is what is currently supported:
```yaml
model_list:
  - model_name: gpt-4
    litellm_params:
      model: openai/fake
      api_key: fake-key
      api_base: https://exampleopenaiendpoint-production.up.railway.app/
      tags: ["free"] # 👈 Key Change
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      tags: ["paid"] # 👈 Key Change
  - model_name: gpt-4
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      api_base: https://exampleopenaiendpoint-production.up.railway.app/
      tags: ["default"] # OPTIONAL - All untagged requests will get routed to this
  

router_settings:
  enable_tag_filtering: True # 👈 Key Change
general_settings: 
  master_key: sk-1234
```
We modify to treat
```yaml
model_list:
  - model_name: nova-embeddings-v1
      litellm_params:
      model: nova-embeddings-retrieval
      api_key: fake-key
      api_base: https://somenovaserver.com/v1
      task: "retrival"]# 👈 Key Change
  - model_name: nova-embeddings-v1
    litellm_params:
      model: nova-embeddings-text-matching
      api_key: os.environ/OPENAI_API_KEY
      task: "text-matching"] # 👈 Key Change
  - model_name: nova-embeddings-v1-code
    litellm_params:
      model: openai/gpt-4o
      api_key: os.environ/OPENAI_API_KEY
      api_base: https://somenovaserver.com/v1
      tags: "code"] #
  

router_settings:
  enable_tag_filtering: True # 👈 Key Change
general_settings: 
  master_key: sk-1234
```

In the above example the user calling litellm proxy is calling [baseurl]/v1/embeddings in all cases.  we are leveraging the proxy's internal routinga bilities to route to the lora-task specific model.  All 3 tasks are served from a single (or individual, it doesn't matter) backend endpoint.  The Nova instance activates the given lora by understanding the given model name (e.g. nova-embeddings-retrieval)


### DOCUMENTATION: /Users/brianbagdasarian/projects/litellm/docs

If you ahve access to graphiti tools store insighes in the "litellm" group id

in /Users/brianbagdasarian/projects/litellm/dev/ARCHITECTURE_DECISIONS.md document architecture decisions
in /Users/brianbagdasarian/projects/litellm/dev/GOTCHAS.md store unexpected findings.
