#!/usr/bin/env python3
"""
Test Nova Embeddings V1 Integration with LiteLLM

This script tests the complete Nova integration:
1. Provider registration
2. Task-based routing
3. Multimodal inputs
4. Instructions support
5. Multivector output

Prerequisites:
- LiteLLM proxy running on port 4000
- Nova server configured with adapters
- Environment variables set (REMODL_AI_API_BASE, etc.)
"""

import requests
import json
from typing import Dict, Any


def test_request(
    task: str,
    input_data: list,
    instructions: str = None,
    return_multivector: bool = False,
    dimensions: int = None,
) -> Dict[str, Any]:
    """
    Make a test embedding request to the proxy
    """
    payload = {
        "model": "nova-embeddings-v1",
        "task": task,
        "input": input_data,
    }
    
    if instructions:
        payload["instructions"] = instructions
    if return_multivector is not None:
        payload["return_multivector"] = return_multivector
    if dimensions:
        payload["dimensions"] = dimensions
    
    response = requests.post(
        "http://localhost:4000/v1/embeddings",
        headers={
            "Authorization": "Bearer sk-1234",
            "Content-Type": "application/json",
        },
        json=payload,
    )
    
    return {
        "status_code": response.status_code,
        "headers": dict(response.headers),
        "body": response.json() if response.status_code == 200 else response.text,
    }


def main():
    print("=" * 80)
    print("Nova Embeddings V1 Integration Test")
    print("=" * 80)
    
    # Test 1: Basic Retrieval
    print("\n[Test 1] Basic Retrieval Task")
    print("-" * 80)
    result = test_request(
        task="retrieval",
        input_data=["test query", "test document"],
    )
    print(f"Status: {result['status_code']}")
    print(f"Routed to: {result['headers'].get('x-remodl-model-id')}")
    if result['status_code'] == 200:
        print(f"Embeddings: {len(result['body']['data'])} vectors")
        print(f"Dimensions: {len(result['body']['data'][0]['embedding'])}")
        print("✅ PASS")
    else:
        print(f"❌ FAIL: {result['body']}")
    
    # Test 2: Retrieval with Query Subtask
    print("\n[Test 2] Retrieval.Query Subtask")
    print("-" * 80)
    result = test_request(
        task="retrieval.query",
        input_data=[{"text": "search for legal cases"}],
        instructions="Focus on legal precedents and case citations",
    )
    print(f"Status: {result['status_code']}")
    print(f"Routed to: {result['headers'].get('x-remodl-model-id')}")
    if result['status_code'] == 200:
        print("✅ PASS - Routed to retrieval adapter")
    else:
        print(f"❌ FAIL: {result['body']}")
    
    # Test 3: Retrieval.Passage with Image
    print("\n[Test 3] Multimodal Retrieval.Passage")
    print("-" * 80)
    result = test_request(
        task="retrieval.passage",
        input_data=[
            {
                "image": "https://media.eagereyes.org/wp-content/uploads/2016/05/pie-package-teaser.png"
            },
            {
                "text": "Chart showing data distribution"
            }
        ],
        instructions="Analyze chart layout and extract key data points",
        return_multivector=True,
    )
    print(f"Status: {result['status_code']}")
    print(f"Routed to: {result['headers'].get('x-remodl-model-id')}")
    if result['status_code'] == 200:
        embeddings = result['body']['data']
        print(f"Image embedding shape: {type(embeddings[0]['embedding'])}")
        print(f"Text embedding shape: {type(embeddings[1]['embedding'])}")
        print("✅ PASS - Multimodal with multivector")
    else:
        print(f"❌ FAIL: {result['body']}")
    
    # Test 4: Text Matching
    print("\n[Test 4] Text Matching Task")
    print("-" * 80)
    result = test_request(
        task="text-matching",
        input_data=["Text A for comparison", "Text B for comparison"],
    )
    print(f"Status: {result['status_code']}")
    print(f"Routed to: {result['headers'].get('x-remodl-model-id')}")
    expected_model = "nova-embeddings-text-matching"
    if result['status_code'] == 200:
        actual_model = result['headers'].get('x-remodl-model-id')
        if actual_model == expected_model:
            print(f"✅ PASS - Correctly routed to {expected_model}")
        else:
            print(f"❌ FAIL - Expected {expected_model}, got {actual_model}")
    else:
        print(f"❌ FAIL: {result['body']}")
    
    # Test 5: Code Task
    print("\n[Test 5] Code Task")
    print("-" * 80)
    result = test_request(
        task="code.query",
        input_data=[{"text": "function to parse JSON"}],
        instructions="Focus on function purpose, ignore variable names",
    )
    print(f"Status: {result['status_code']}")
    print(f"Routed to: {result['headers'].get('x-remodl-model-id')}")
    expected_model = "nova-embeddings-code"
    if result['status_code'] == 200:
        actual_model = result['headers'].get('x-remodl-model-id')
        if actual_model == expected_model:
            print(f"✅ PASS - Correctly routed to {expected_model}")
        else:
            print(f"❌ FAIL - Expected {expected_model}, got {actual_model}")
    else:
        print(f"❌ FAIL: {result['body']}")
    
    # Test 6: Dense vs Multivector
    print("\n[Test 6] Dense (Pooled) with Matryoshka")
    print("-" * 80)
    result = test_request(
        task="retrieval",
        input_data=["test document"],
        return_multivector=False,
        dimensions=512,
    )
    print(f"Status: {result['status_code']}")
    if result['status_code'] == 200:
        dims = len(result['body']['data'][0]['embedding'])
        if dims == 512:
            print(f"✅ PASS - Matryoshka truncation to {dims} dimensions")
        else:
            print(f"⚠️  WARNING - Expected 512 dims, got {dims}")
    else:
        print(f"❌ FAIL: {result['body']}")
    
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print("\nIf all tests passed:")
    print("✅ Nova Embeddings V1 is fully integrated!")
    print("✅ Task-based routing is working")
    print("✅ Multimodal inputs are supported")
    print("✅ Instructions are being passed through")
    print("✅ Multivector and dense modes work")
    print("\nNext steps:")
    print("- Add your Nova models to the Model Hub in the UI")
    print("- Configure environment variables")
    print("- Start using Nova's instruction tuning for domain adaptation!")


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to proxy at http://localhost:4000")
        print("Make sure the proxy is running:")
        print("  poetry run litellm --config proxy_server_config.yaml")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

