# Nova Embeddings V1 - Quick Start Guide

## Overview

Nova Embeddings V1 (`remodlai/nova-embeddings-v1`) is now fully integrated into LiteLLM with support for:

✨ **Runtime Instruction Tuning** - Adapt to any domain at query time  
🎯 **Task Adapters** - retrieval, text-matching, code  
🔢 **Dense & Multivector** - Pooled (up to 2048d) or token-level (128d)  
🖼️ **Multimodal** - Text, images, and code  
🚀 **Production-Ready** - Sub-20ms P50, 400+ req/s

## Setup

### 1. Environment Variables

Create a `.env` file:

```bash
# Hosted Lexiq Nova
HOSTED_LEXIQ_NOVA_API_BASE=https://api.lexiq-nova.com
HOSTED_LEXIQ_NOVA_API_KEY=your-api-key-here
```

### 2. Start the Proxy

```bash
# Make sure you've restarted the proxy to load the new configuration
poetry run litellm --config proxy_server_config.yaml
```

### 3. Test the Endpoint

```bash
curl -X POST http://localhost:4000/v1/embeddings \
  -H "Authorization: Bearer sk-1234" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "nova-embeddings-v1",
    "task": "retrieval",
    "input": ["test query", "test document"]
  }'
```

## Usage Examples

### Basic Embedding

```python
import litellm

response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    input=["Hello world", "How are you?"],
    task="retrieval"
)

print(response['data'][0]['embedding'][:5])  # First 5 dimensions
```

### With Runtime Instructions (Domain Adaptation)

```python
# Legal domain
legal_response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    instructions="Focus on case law, statutory citations, and judicial precedents",
    task="retrieval",
    input=[
        {"task": "retrieval.query", "text": "trademark dilution doctrine"},
        {"task": "retrieval.passage", "text": "Under the Lanham Act..."}
    ]
)

# Medical domain - same model, different instructions
medical_response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    instructions="Prioritize clinical evidence and treatment protocols",
    task="retrieval",
    input=["patient presents with acute symptoms"]
)
```

### Multivector (Token-Level) for Late Interaction

```python
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    task="retrieval",
    return_multivector=True,  # Returns 128d per token
    input=["long document for precise matching"]
)

# Each token gets its own 128d vector
print(f"Tokens: {len(response['data'][0]['embedding'])}")
print(f"Dimensions per token: {len(response['data'][0]['embedding'][0])}")
```

### Dense (Pooled) with Matryoshka Dimensions

```python
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    task="retrieval",
    return_multivector=False,  # Pooled vector
    dimensions=512,  # Matryoshka truncation (256/512/1024/2048)
    input=["document text"]
)

print(f"Dimensions: {len(response['data'][0]['embedding'])}")  # 512
```

### Multimodal (Text + Images)

```python
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    task="retrieval",
    instructions="Extract technical specifications from charts",
    input=[
        {
            "text": "Analyze this performance chart",
            "image": "https://example.com/chart.png"
        },
        {
            "text": "Revenue trends Q4 2024"
        }
    ]
)
```

### Code Search

```python
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    task="code",
    adapter="code",
    instructions="Focus on function signatures and API patterns",
    input=[
        {"task": "code.query", "text": "function to parse JSON"},
        {"task": "code.passage", "text": "def parse_json(data): return json.loads(data)"}
    ]
)
```

## Performance Gains

Using instructions improves domain-specific retrieval:

| Domain | Metric | Without Instructions | With Instructions | Gain |
|--------|--------|---------------------|-------------------|------|
| Legal | P@10 | 62.3% | 79.1% | **+27%** |
| Medical | NDCG@20 | 0.701 | 0.843 | **+20%** |
| Finance | MRR | 0.554 | 0.712 | **+29%** |
| Code | EM@5 | 41.2% | 53.8% | **+31%** |

## Available Models

All models are now available via the proxy:

```
nova-embeddings-v1                           # Alias
hosted_lexiq_nova/nova-embeddings-v1         # Short form  
hosted_lexiq_nova/remodlai/nova-embeddings-v1  # Full path
```

## Task Adapters

| Task | Adapter | Use Case |
|------|---------|----------|
| `retrieval` | retrieval | General search, document retrieval |
| `text-matching` | text-matching | Semantic similarity, clustering |
| `code` | code | Code search, function matching |

Per-item overrides:
- `retrieval.query` - Search query
- `retrieval.passage` - Document/passage to index
- `code.query` - Code search query
- `code.passage` - Code snippet to index

## Tips

✅ **Use specific instructions** - "Focus on case law citations" beats "be accurate"  
✅ **Match query/passage tasks** - Query: `retrieval.query`, Docs: `retrieval.passage`  
✅ **Multivector for precision** - Use when exact token matching matters  
✅ **Dense for speed** - Use pooled vectors for fast approximate search  
✅ **Lower dimensions for cost** - 256d or 512d often sufficient vs 2048d  

## Troubleshooting

**Q: Model not found**  
A: Restart the proxy after updating the config: `Ctrl+C` then `poetry run litellm --config proxy_server_config.yaml`

**Q: Models not showing in UI**  
A: Restart the UI dev server: `cd ui/litellm-dashboard && npm run dev`

**Q: Instruction parameter ignored**  
A: Check that your API endpoint supports Nova's extended parameters

## Next Steps

1. Set environment variables in `.env`
2. Restart the proxy
3. Test with the examples above
4. Monitor performance improvements with your specific domain instructions

For full documentation, see:
- `litellm/llms/hosted_lexiq_nova/embedding/README.md`
- Model card: https://huggingface.co/remodlai/nova-embeddings-v1

