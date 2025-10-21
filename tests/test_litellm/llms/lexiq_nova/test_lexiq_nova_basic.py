"""
Basic tests for Lexiq Nova provider

Note: Lexiq Nova uses the same transformation as hosted_lexiq_nova
"""
import os
import sys

import pytest

sys.path.insert(
    0, os.path.abspath("../../../..")
)  # Adds the parent directory to the system path

from litellm.llms.lexiq_nova.completion.transformation import LexiqNovaConfig
from litellm.llms.hosted_lexiq_nova.chat.transformation import HostedLexiqNovaChatConfig


def test_lexiq_nova_inherits_from_hosted():
    """Test that LexiqNovaConfig properly inherits from HostedLexiqNovaChatConfig"""
    config = LexiqNovaConfig()
    assert isinstance(config, HostedLexiqNovaChatConfig)
    
    # Test that it has the same supported params
    supported_params = config.get_supported_openai_params(model="lexiq_nova/test-model")
    assert "reasoning_effort" in supported_params


def test_lexiq_nova_passthrough_config():
    """Test that passthrough config exists"""
    from litellm.llms.lexiq_nova.passthrough.transformation import LexiqNovaPassthroughConfig
    
    config = LexiqNovaPassthroughConfig()
    assert config is not None
    
    # Test is_streaming_request method
    assert config.is_streaming_request("/v1/chat/completions", {"stream": True}) is True
    assert config.is_streaming_request("/v1/chat/completions", {"stream": False}) is False

