"""
Register Nova Embeddings V1 models with LiteLLM

Run this after starting the proxy to register the nova-embeddings-v1 models.
"""

import litellm

# Register nova-embeddings-v1 models
nova_embedding_models = {
    "nova-embeddings-v1": {
        "input_cost_per_image": 5e-06,
        "input_cost_per_token": 5e-06,
        "litellm_provider": "remodlai-embedding-models",
        "max_input_tokens": 8192,
        "max_output_tokens": 8192,
        "max_tokens": 8192,
        "mode": "embedding",
        "output_cost_per_token": 1.5e-05,
        "supports_function_calling": False,
        "supports_tool_choice": False,
        "supports_vision": True,
        "supports_web_search": False,
        "supports_embedding_image_input": True,
        "supports_embedding_text_input": True,
        "supports_embedding_multivector": True,
        "supports_instructions": True,
        "output_vector_size": 2048,
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
        # trunk-ignore(ruff/T201)
        print(f"   Output vector size: {model_info.get('output_vector_size')}")
        print(f"   Multimodal: {model_info.get('supports_embedding_image_input')}")
    except Exception as e:
        print(f"\n❌ {model_name}: {e}")

print("\n✅ Nova Embeddings V1 registration complete!")
print("\nYou can now use these models:")
print(
    "  litellm.embedding(model='remodlai/nova-embeddings-v1', input=[...], task='retrieval')"
)
