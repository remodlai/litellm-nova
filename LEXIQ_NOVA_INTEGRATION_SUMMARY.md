# Lexiq Nova Integration Summary

This document summarizes the complete integration of `lexiq_nova` and `hosted_lexiq_nova` providers into LiteLLM, following the vllm/hosted_vllm pattern.

## Overview

The integration adds two new providers to LiteLLM:
- **lexiq_nova**: Local SDK-based provider (mirrors vllm)
- **hosted_lexiq_nova**: Hosted API provider (mirrors hosted_vllm)

Both providers are fully OpenAI-compatible and support all standard LiteLLM features including chat completions, embeddings, rerank, transcriptions, and the OpenAI Responses API.

## Files Created

### Core Provider Files

#### lexiq_nova/
- `litellm/llms/lexiq_nova/common_utils.py` - Error handling and model info
- `litellm/llms/lexiq_nova/completion/handler.py` - Completion handler (uses vllm SDK)
- `litellm/llms/lexiq_nova/completion/transformation.py` - Inherits from HostedLexiqNovaChatConfig
- `litellm/llms/lexiq_nova/passthrough/transformation.py` - Passthrough config for proxy
- `litellm/llms/lexiq_nova/responses/transformation.py` - OpenAI Responses API support

#### hosted_lexiq_nova/
- `litellm/llms/hosted_lexiq_nova/chat/transformation.py` - Chat completions config (OpenAI-compatible)
- `litellm/llms/hosted_lexiq_nova/embedding/README.md` - Embedding docs (OpenAI superset)
- `litellm/llms/hosted_lexiq_nova/rerank/transformation.py` - Rerank functionality
- `litellm/llms/hosted_lexiq_nova/transcriptions/transformation.py` - Audio transcription support
- `litellm/llms/hosted_lexiq_nova/responses/transformation.py` - OpenAI Responses API support

### Test Files
- `tests/test_litellm/llms/lexiq_nova/test_lexiq_nova_basic.py`
- `tests/test_litellm/llms/hosted_lexiq_nova/chat/test_hosted_lexiq_nova_chat_transformation.py`
- `tests/test_litellm/llms/hosted_lexiq_nova/test_hosted_lexiq_nova_rerank_transformation.py`

## Files Modified

### Core Integration Files

1. **litellm/__init__.py**
   - Added `lexiq_nova_key` and `hosted_lexiq_nova_key` API key variables (lines 255-256)
   - Added imports for `LexiqNovaConfig` and `HostedLexiqNovaChatConfig` (lines 1275, 1279)

2. **litellm/constants.py**
   - Added `lexiq_nova` to LITELLM_CHAT_PROVIDERS (line 299)
   - Added `hosted_lexiq_nova` to LITELLM_CHAT_PROVIDERS (line 332)
   - Added `hosted_lexiq_nova` to LITELLM_EMBEDDING_PROVIDERS_SUPPORTING_INPUT_ARRAY_OF_TOKENS (line 360)
   - Added `hosted_lexiq_nova` to openai_compatible_providers (line 520)
   - Added `hosted_lexiq_nova` to openai_text_completion_compatible_providers (line 547)

3. **litellm/main.py**
   - Added import for `lexiq_nova_handler` (line 203)
   - Added routing logic for `lexiq_nova` provider (lines 3328-3356)
   - Added `hosted_lexiq_nova` to OpenAI-like providers check (line 4221)

4. **litellm/litellm_core_utils/get_llm_provider_logic.py**
   - Added model prefix handling for `lexiq_nova/` (lines 372-375)

5. **litellm/types/utils.py**
   - Added `LEXIQ_NOVA` and `HOSTED_LEXIQ_NOVA` to LlmProviders enum (lines 2504-2505)

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

# Using hosted_lexiq_nova
response = litellm.completion(
    model="hosted_lexiq_nova/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}],
    api_base="https://api.lexiq-nova.com",
    api_key="your-api-key"
)

# Using lexiq_nova (local SDK)
response = litellm.completion(
    model="lexiq_nova/llama-3.1-70b-instruct",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### Environment Variables

```bash
# Hosted Lexiq Nova
export HOSTED_LEXIQ_NOVA_API_BASE="https://api.lexiq-nova.com"
export HOSTED_LEXIQ_NOVA_API_KEY="your-api-key"

# Lexiq Nova (local)
export LEXIQ_NOVA_API_BASE="http://localhost:8000"
```

### OpenAI Responses API

```python
import litellm

response = litellm.create_response(
    model="hosted_lexiq_nova/o1-preview",
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
    model="hosted_lexiq_nova/rerank-model",
    query="What is machine learning?",
    documents=["ML is...", "AI is...", "DL is..."],
    top_n=2,
    api_base="https://api.lexiq-nova.com"
)
```

## Model Name Patterns

The integration follows LiteLLM's standard model naming conventions:

- **Hosted**: `hosted_lexiq_nova/<model-name>`
- **Local**: `lexiq_nova/<model-name>`

Examples:
- `hosted_lexiq_nova/llama-3.1-70b-instruct`
- `hosted_lexiq_nova/gpt-oss-120b`
- `lexiq_nova/facebook/opt-125m`

## Configuration

### Proxy Configuration

```yaml
model_list:
  - model_name: lexiq-nova-chat
    litellm_params:
      model: hosted_lexiq_nova/llama-3.1-70b-instruct
      api_base: https://api.lexiq-nova.com
      api_key: os.environ/HOSTED_LEXIQ_NOVA_API_KEY
```

### Router Configuration

```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "lexiq-nova",
            "litellm_params": {
                "model": "hosted_lexiq_nova/llama-3.1-70b-instruct",
                "api_base": "https://api.lexiq-nova.com",
                "api_key": os.getenv("HOSTED_LEXIQ_NOVA_API_KEY")
            }
        }
    ]
)
```

## Architecture

The integration follows the established LiteLLM pattern:

1. **lexiq_nova** (Local SDK):
   - Inherits from `hosted_lexiq_nova` transformations
   - Uses vllm SDK for local inference
   - Minimal transformation layer

2. **hosted_lexiq_nova** (API):
   - Extends `OpenAIGPTConfig` for OpenAI compatibility
   - Custom environment validation
   - Provider-specific parameter handling
   - Error handling via custom exception classes

## Testing

Run tests with:

```bash
# All lexiq_nova tests
pytest tests/test_litellm/llms/lexiq_nova/ -v

# All hosted_lexiq_nova tests
pytest tests/test_litellm/llms/hosted_lexiq_nova/ -v

# Specific test
pytest tests/test_litellm/llms/hosted_lexiq_nova/chat/test_hosted_lexiq_nova_chat_transformation.py::test_hosted_lexiq_nova_supports_reasoning_effort -v
```

## Migration from VLLM

If you're currently using vllm or hosted_vllm, migrating to lexiq_nova is simple:

```python
# Before (vllm)
response = litellm.completion(
    model="hosted_vllm/my-model",
    messages=[...]
)

# After (lexiq_nova)
response = litellm.completion(
    model="hosted_lexiq_nova/my-model",
    messages=[...]
)
```

All parameters, features, and behaviors are identical.

## Notes

- **Production Use**: Use `hosted_lexiq_nova` for production deployments
- **Development**: `lexiq_nova` is suitable for local testing with the vllm SDK
- **API Compatibility**: Both providers are 100% OpenAI-compatible
- **Feature Parity**: All features supported by hosted_vllm are supported by hosted_lexiq_nova

## Future Enhancements

Potential areas for future development:
- Custom cost tracking rules
- Provider-specific optimization flags
- Enhanced streaming capabilities
- Additional endpoint support (assistants, fine-tuning, etc.)

## Contact

For issues or questions about the Lexiq Nova integration, please refer to the LiteLLM documentation at https://docs.litellm.ai/

