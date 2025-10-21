# Hosted Lexiq Nova Embeddings

Lexiq Nova provides **Nova Embeddings V1** - the industry's first multimodal multi-vector embeddings with runtime instruction tuning.

## Key Features

✨ **Runtime Instruction Tuning** - Adapt embeddings to any domain at query time  
🎯 **Task-Specific Adapters** - Retrieval, text-matching, and code search  
🔢 **Dense & Multi-Vector** - Token-level (128d) or pooled (up to 2048d with matryoshka)  
🖼️ **Multimodal** - Text, images, and code in unified API  
🚀 **Production-Ready** - Sub-20ms P50 latency, 400+ req/s throughput

## Supported Parameters

Nova extends OpenAI's embedding API with:

| Parameter | Type | Description |
|-----------|------|-------------|
| `instructions` | string | Custom domain instructions (legal, medical, financial, etc.) |
| `task` | string | Required: `"retrieval"`, `"text-matching"`, or `"code"` |
| `return_multivector` | boolean | `true` for token-level (128d), `false` for pooled |
| `dimensions` | integer | Matryoshka truncation (256/512/1024/2048) when pooled |
| `adapter` | string | Per-item adapter override |
| `image` | string/bytes | URL, base64, or bytes for multimodal |
| `image_embeds` | list | Precomputed vision embeddings |

## Usage Examples

### Basic Dense Embeddings
```python
import litellm

response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    input=["search query", "document text"],
    task="retrieval",
    return_multivector=False,
    dimensions=512
)
```

### With Domain Instructions
```python
# Legal domain
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    instructions="Focus on case law, statutory citations, and judicial precedents",
    task="retrieval",
    input=[
        {"task": "retrieval.query", "text": "contract breach remedies"},
        {"task": "retrieval.passage", "text": "Under UCC §2-711..."}
    ]
)
```

### Multivector (Token-Level) Embeddings
```python
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    task="retrieval",
    return_multivector=True,  # Returns 128d per token
    input=["long document for late interaction"]
)
```

### Multimodal with Images
```python
response = litellm.embedding(
    model="hosted_lexiq_nova/nova-embeddings-v1",
    task="retrieval",
    instructions="Extract technical specifications from charts",
    input=[
        {
            "text": "Analyze this performance chart",
            "image": "https://example.com/chart.png"
        }
    ]
)
```

## Performance Gains

Using instructions improves domain-specific retrieval by **15-40%**:
- Legal documents: +27% precision@10
- Medical abstracts: +20% NDCG@20  
- Financial filings: +29% MRR
- Code search: +31% exact match@5

To pass additional provider-specific parameters, see [this](https://docs.litellm.ai/docs/completion/provider_specific_params)
