"""
Register Nova Embeddings V1 models with LiteLLM

Run this after starting the proxy to register the nova-embeddings-v1 models.
"""

import litellm

# Register nova-embeddings-v1 models
nova_embedding_models = {
    "remodlai/nova-embeddings-v1": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "litellm_provider": "remodlai",
        "mode": "embedding",
        "max_input_tokens": 8192,
        "max_tokens": 8192,
        "output_vector_size": 128,
        "supports_embedding_image_input": True,
        "metadata": {
            "notes": "Multivector, multimodal embedding model. Alias for remodlai/nova-embeddings-v1."
        }
    },
    "remodlai/remodlai/nova-embeddings-v1": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "litellm_provider": "remodlai",
        "mode": "embedding",
        "max_input_tokens": 8192,
        "max_tokens": 8192,
        "output_vector_size": 128,
        "supports_embedding_image_input": True,
        "metadata": {
            "notes": "Nova Embeddings V1: Industry-first multimodal multi-vector embeddings with runtime instruction tuning. Supports text, images, code. Task adapters: retrieval, text-matching, code. Dense (pooled up to 2048d) or multivector (128d per token)."
        }
    },
    "remodlai/nova-embeddings-v1": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "litellm_provider": "remodlai",
        "mode": "embedding",
        "max_input_tokens": 8192,
        "max_tokens": 8192,
        "output_vector_size": 128,
        "supports_embedding_image_input": True,
        "metadata": {
            "notes": "Local SDK version. Alias for remodlai/nova-embeddings-v1."
        }
    },
    "remodlai/remodlai/nova-embeddings-v1": {
        "input_cost_per_token": 0.0,
        "output_cost_per_token": 0.0,
        "litellm_provider": "remodlai",
        "mode": "embedding",
        "max_input_tokens": 8192,
        "max_tokens": 8192,
        "output_vector_size": 128,
        "supports_embedding_image_input": True,
        "metadata": {
            "notes": "Local SDK version. Multivector, multimodal embedding model."
        }
    }
}

# Register the models
litellm.register_model(nova_embedding_models)

print("✅ Registered Nova Embeddings V1 models:")
for model_name in nova_embedding_models.keys():
    print(f"  - {model_name}")

# Verify registration
for model_name in nova_embedding_models.keys():
    try:
        model_info = litellm.get_model_info(model_name)
        print(f"\n✅ {model_name}")
        print(f"   Provider: {model_info.get('litellm_provider')}")
        print(f"   Max tokens: {model_info.get('max_tokens')}")
        print(f"   Output vector size: {model_info.get('output_vector_size')}")
        print(f"   Multimodal: {model_info.get('supports_embedding_image_input')}")
    except Exception as e:
        print(f"\n❌ {model_name}: {e}")

print("\n✅ Nova Embeddings V1 registration complete!")
print("\nYou can now use these models:")
print("  litellm.embedding(model='remodlai/nova-embeddings-v1', input=[...], task='retrieval')")

