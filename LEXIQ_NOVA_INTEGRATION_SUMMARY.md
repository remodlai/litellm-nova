# Lexiq Nova Integration Summary

This document summarizes the complete integration of `remodlai` and `remodlai` providers into LiteLLM, following the vllm/hosted_vllm pattern.

## Overview

The integration adds two new providers to LiteLLM:
- **remodlai**: Local SDK-based provider (mirrors vllm)
- **remodlai**: Hosted API provider (mirrors hosted_vllm)

Both providers are fully OpenAI-compatible and support all standard LiteLLM features including chat completions, embeddings, rerank, transcriptions, and the OpenAI Responses API.

## Files Created

### Core Provider Files

#### remodlai/
- `litellm/llms/remodlai/common_utils.py` - Error handling and model info
- `litellm/llms/remodlai/completion/handler.py` - Completion handler (uses vllm SDK)
- `litellm/llms/remodlai/completion/transformation.py` - Inherits from HostedLexiqNovaChatConfig
- `litellm/llms/remodlai/passthrough/transformation.py` - Passthrough config for proxy
- `litellm/llms/remodlai/responses/transformation.py` - OpenAI Responses API support

#### remodlai/
- `litellm/llms/remodlai/chat/transformation.py` - Chat completions config (OpenAI-compatible)
- `litellm/llms/remodlai/embedding/README.md` - Embedding docs (OpenAI superset)
- `litellm/llms/remodlai/rerank/transformation.py` - Rerank functionality
- `litellm/llms/remodlai/transcriptions/transformation.py` - Audio transcription support
- `litellm/llms/remodlai/responses/transformation.py` - OpenAI Responses API support

### Test Files
- `tests/test_litellm/llms/remodlai/test_remodlai_basic.py`
- `tests/test_litellm/llms/remodlai/chat/test_remodlai_chat_transformation.py`
- `tests/test_litellm/llms/remodlai/test_remodlai_rerank_transformation.py`

## Files Modified

### Core Integration Files

1. **litellm/__init__.py**
   - Added `remodlai_key` and `remodlai_key` API key variables (lines 255-256)
   - Added imports for `LexiqNovaConfig` and `HostedLexiqNovaChatConfig` (lines 1275, 1279)

2. **litellm/constants.py**
   - Added `remodlai` to LITELLM_CHAT_PROVIDERS (line 299)
   - Added `remodlai` to LITELLM_CHAT_PROVIDERS (line 332)
   - Added `remodlai` to LITELLM_EMBEDDING_PROVIDERS_SUPPORTING_INPUT_ARRAY_OF_TOKENS (line 360)
   - Added `remodlai` to openai_compatible_providers (line 520)
   - Added `remodlai` to openai_text_completion_compatible_providers (line 547)

3. **litellm/main.py**
   - Added import for `remodlai_handler` (line 203)
   - Added routing logic for `remodlai` provider (lines 3328-3356)
   - Added `remodlai` to OpenAI-like providers check (line 4221)

4. **litellm/litellm_core_utils/get_llm_provider_logic.py**
   - Added model prefix handling for `remodlai/` (lines 372-375)

5. **litellm/types/utils.py**
   - Added `LEXIQ_NOVA` and `REMODLAI` to LlmProviders enum (lines 2504-2505)

## Features Supported

### Chat Completions
- ✅ Standard chat completions
- ✅ Streaming responses
- ✅ Function/tool calling
- ✅ Vision (video files via file_id/file_data)
- ✅ Audio input/output
- ✅ Reasoning effort parameter
- ✅ OpenAI Responses API

### Embeddings
- ✅ Text embeddings
- ✅ Input as array of tokens
- ✅ OpenAI-compatible interface

### Rerank
- ✅ Document reranking
- ✅ Cohere-compatible API
- ✅ Top-N filtering
- ✅ Rank fields support

### Transcriptions
- ✅ Audio transcription
- ✅ Whisper-compatible API
- ✅ OpenAI audio/transcriptions endpoint

### Additional Features
- ✅ Passthrough mode for proxy
- ✅ API key management
- ✅ Error handling
- ✅ Cost tracking
- ✅ Logging/observability

## Usage Examples

### Basic Chat Completion

```python
import litellm

# Using remodlai
response = litellm.completion(
    model="remodlai/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="https://api.lexiq-nova.com",
    api_key="your-api-key"
)

# Using remodlai (local SDK)
response = litellm.completion(
    model="remodlai/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Environment Variables

```bash
# Hosted Lexiq Nova
export REMODLAI_API_BASE="https://api.lexiq-nova.com"
export REMODLAI_API_KEY="your-api-key"

# Lexiq Nova (local)
export LEXIQ_NOVA_API_BASE="http://localhost:8000"
```

### OpenAI Responses API

```python
import litellm

response = litellm.create_response(
    model="remodlai/o1-preview",
    input=[
        {
            "type": "user",
            "content": "What is the meaning of life?"
        }
    ],
    api_base="https://api.lexiq-nova.com",
    api_key="your-api-key"
)
```

### Rerank

```python
import litellm

response = litellm.rerank(
    model="remodlai/rerank-model",
    query="What is machine learning?",
    documents=["ML is...", "AI is...", "DL is..."],
    top_n=2,
    api_base="https://api.lexiq-nova.com"
)
```

## Model Name Patterns

The integration follows LiteLLM's standard model naming conventions:

- **Hosted**: `remodlai/<model-name>`
- **Local**: `remodlai/<model-name>`

Examples:
- `remodlai/llama-3.1-70b-instruct`
- `remodlai/gpt-oss-120b`
- `remodlai/facebook/opt-125m`

## Configuration

### Proxy Configuration

```yaml
model_list:
  - model_name: lexiq-nova-chat
    litellm_params:
      model: remodlai/llama-3.1-70b-instruct
      api_base: https://api.lexiq-nova.com
      api_key: os.environ/REMODLAI_API_KEY
```

### Router Configuration

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "lexiq-nova",
            "litellm_params": {
                "model": "remodlai/llama-3.1-70b-instruct",
                "api_base": "https://api.lexiq-nova.com",
                "api_key": os.getenv("REMODLAI_API_KEY")
            }
        }
    ]
)
```

## Architecture

The integration follows the established LiteLLM pattern:

1. **remodlai** (Local SDK):
   - Inherits from `remodlai` transformations
   - Uses vllm SDK for local inference
   - Minimal transformation layer

2. **remodlai** (API):
   - Extends `OpenAIGPTConfig` for OpenAI compatibility
   - Custom environment validation
   - Provider-specific parameter handling
   - Error handling via custom exception classes

## Testing

Run tests with:

```bash
# All remodlai tests
pytest tests/test_litellm/llms/remodlai/ -v

# All remodlai tests
pytest tests/test_litellm/llms/remodlai/ -v

# Specific test
pytest tests/test_litellm/llms/remodlai/chat/test_remodlai_chat_transformation.py::test_remodlai_supports_reasoning_effort -v
```

## Migration from VLLM

If you're currently using vllm or hosted_vllm, migrating to remodlai is simple:

```python
# Before (vllm)
response = litellm.completion(
    model="hosted_vllm/my-model",
    messages=[...]
)

# After (remodlai)
response = litellm.completion(
    model="remodlai/my-model",
    messages=[...]
)
```

All parameters, features, and behaviors are identical.

## Notes

- **Production Use**: Use `remodlai` for production deployments
- **Development**: `remodlai` is suitable for local testing with the vllm SDK
- **API Compatibility**: Both providers are 100% OpenAI-compatible
- **Feature Parity**: All features supported by hosted_vllm are supported by remodlai

## Future Enhancements

Potential areas for future development:
- Custom cost tracking rules
- Provider-specific optimization flags
- Enhanced streaming capabilities
- Additional endpoint support (assistants, fine-tuning, etc.)

## Contact

For issues or questions about the Lexiq Nova integration, please refer to the LiteLLM documentation at https://docs.litellm.ai/

