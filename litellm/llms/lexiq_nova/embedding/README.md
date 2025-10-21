# Lexiq Nova Embeddings (Local SDK)

**For production deployments, use `hosted_lexiq_nova` instead.**

This is the local SDK version for development/testing with the vllm SDK.

Supports all the same features as `hosted_lexiq_nova/nova-embeddings-v1`:
- Runtime instruction tuning
- Task-specific adapters (retrieval, text-matching, code)
- Dense & multi-vector embeddings
- Multimodal (text + images)
- Matryoshka dimensions

See `hosted_lexiq_nova/embedding/README.md` for full documentation.

To pass provider-specific parameters, see [this](https://docs.litellm.ai/docs/completion/provider_specific_params)

