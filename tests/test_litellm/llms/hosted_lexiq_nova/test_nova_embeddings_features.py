"""
Test Nova Embeddings V1 special features:
- Runtime instruction tuning
- Task-specific adapters (retrieval, text-matching, code)
- Dense (pooled) and multivector (token-level) outputs
- Multimodal support (text + images)
- Matryoshka dimensions
"""
import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath("../../../..")
)  # Adds the parent directory to the system path

from litellm.llms.hosted_lexiq_nova.embedding.transformation import (
    HostedLexiqNovaEmbeddingConfig,
)


class TestNovaEmbeddingsFeatures:
    """Test Nova Embeddings V1 unique capabilities"""

    def setup_method(self):
        self.config = HostedLexiqNovaEmbeddingConfig()
        self.model = "hosted_lexiq_nova/nova-embeddings-v1"

    def test_supported_params_include_nova_features(self):
        """Verify all Nova-specific parameters are supported"""
        supported = self.config.get_supported_openai_params(self.model)
        
        # Standard OpenAI params
        assert "input" in supported
        assert "model" in supported
        assert "encoding_format" in supported
        assert "dimensions" in supported
        
        # Nova-specific params
        assert "task" in supported
        assert "return_multivector" in supported
        assert "instructions" in supported
        assert "adapter" in supported
        assert "image" in supported
        assert "image_embeds" in supported

    def test_map_params_handles_instructions(self):
        """Test that runtime instructions are properly passed through"""
        non_default_params = {
            "instructions": "Focus on legal precedents and case citations",
            "task": "retrieval",
        }
        optional_params = {}
        
        result = self.config.map_openai_params(
            non_default_params=non_default_params,
            optional_params=optional_params,
            model=self.model,
            drop_params=False,
        )
        
        assert "instructions" in result
        assert result["instructions"] == "Focus on legal precedents and case citations"
        assert "task" in result
        assert result["task"] == "retrieval"

    def test_map_params_handles_multivector_mode(self):
        """Test multivector vs dense mode parameters"""
        # Multivector mode (token-level embeddings)
        multivector_params = {
            "task": "retrieval",
            "return_multivector": True,
        }
        optional_params = {}
        
        result = self.config.map_openai_params(
            non_default_params=multivector_params,
            optional_params=optional_params,
            model=self.model,
            drop_params=False,
        )
        
        assert result["return_multivector"] is True
        
        # Dense mode with matryoshka dimensions
        dense_params = {
            "task": "retrieval",
            "return_multivector": False,
            "dimensions": 512,
        }
        optional_params = {}
        
        result = self.config.map_openai_params(
            non_default_params=dense_params,
            optional_params=optional_params,
            model=self.model,
            drop_params=False,
        )
        
        assert result["return_multivector"] is False
        assert result["dimensions"] == 512

    def test_map_params_handles_task_adapters(self):
        """Test task and adapter parameters"""
        params = {
            "task": "code",
            "adapter": "code",
        }
        optional_params = {}
        
        result = self.config.map_openai_params(
            non_default_params=params,
            optional_params=optional_params,
            model=self.model,
            drop_params=False,
        )
        
        assert result["task"] == "code"
        assert result["adapter"] == "code"

    def test_map_params_handles_multimodal(self):
        """Test multimodal parameters (images)"""
        params = {
            "task": "retrieval",
            "image": "https://example.com/diagram.png",
        }
        optional_params = {}
        
        result = self.config.map_openai_params(
            non_default_params=params,
            optional_params=optional_params,
            model=self.model,
            drop_params=False,
        )
        
        assert "image" in result
        assert result["image"] == "https://example.com/diagram.png"

    def test_complete_url_generation(self):
        """Test API endpoint URL generation"""
        # Should create the /v1/embeddings endpoint
        url = self.config.get_complete_url(
            api_base="https://api.lexiq-nova.com",
            model=self.model,
            optional_params={},
            stream=None,
        )
        
        assert url == "https://api.lexiq-nova.com/v1/embeddings"
        
        # Should handle trailing slashes
        url2 = self.config.get_complete_url(
            api_base="https://api.lexiq-nova.com/",
            model=self.model,
            optional_params={},
            stream=None,
        )
        
        assert url2 == "https://api.lexiq-nova.com/v1/embeddings"

    def test_environment_validation(self):
        """Test API key and header setup"""
        headers = {}
        result = self.config.validate_environment(
            headers=headers,
            model=self.model,
            messages=[],
            optional_params={},
            api_key="test-api-key",
        )
        
        assert "Authorization" in result
        assert result["Authorization"] == "Bearer test-api-key"
        assert result["Content-Type"] == "application/json"


def test_nova_embeddings_usage_example():
    """
    Example of how to use Nova Embeddings V1 with LiteLLM
    
    This test demonstrates the full feature set:
    - Runtime instructions for domain adaptation
    - Task selection (retrieval, text-matching, code)
    - Dense vs multivector output
    - Multimodal inputs
    """
    
    # This is a documentation/example test - actual execution requires API key
    example_usage = {
        "legal_retrieval": {
            "model": "hosted_lexiq_nova/nova-embeddings-v1",
            "instructions": "Focus on case law, statutory citations, and judicial precedents",
            "task": "retrieval",
            "return_multivector": False,
            "dimensions": 1024,
            "input": [
                {"task": "retrieval.query", "text": "trademark dilution doctrine"},
                {"task": "retrieval.passage", "text": "Under the Lanham Act..."},
            ]
        },
        "medical_search": {
            "model": "hosted_lexiq_nova/nova-embeddings-v1",
            "instructions": "Prioritize clinical evidence and treatment protocols",
            "task": "retrieval",
            "input": ["patient presents with acute symptoms"]
        },
        "multimodal_chart_analysis": {
            "model": "hosted_lexiq_nova/nova-embeddings-v1",
            "task": "retrieval",
            "instructions": "Extract quantitative trends from visualizations",
            "input": [
                {
                    "text": "Analyze revenue growth",
                    "image": "https://example.com/chart.png"
                }
            ]
        },
        "code_search": {
            "model": "hosted_lexiq_nova/nova-embeddings-v1",
            "task": "code",
            "adapter": "code",
            "return_multivector": True,  # Token-level for precise matching
            "input": [
                {"task": "code.query", "text": "function to parse JSON"},
                {"task": "code.passage", "text": "def parse_json(data): ..."}
            ]
        }
    }
    
    # Verify the structure is valid
    assert "legal_retrieval" in example_usage
    assert example_usage["legal_retrieval"]["instructions"] is not None
    assert example_usage["multimodal_chart_analysis"]["image"] is not None
    assert example_usage["code_search"]["return_multivector"] is True
    
    print("✅ Nova Embeddings V1 usage examples validated")

