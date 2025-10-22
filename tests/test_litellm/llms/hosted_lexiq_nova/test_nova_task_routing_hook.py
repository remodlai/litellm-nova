"""
Test Nova Task Routing Hook

Verifies that the task parameter is correctly converted to tags
for routing to the appropriate Nova adapter.
"""
import pytest
from unittest.mock import MagicMock

from litellm.proxy.hooks.nova_task_routing import NovaTaskRoutingHook


class TestNovaTaskRoutingHook:
    """Test the Nova task → tag conversion hook"""

    def setup_method(self):
        self.hook = NovaTaskRoutingHook()
        self.user_api_key_dict = MagicMock()
        self.cache = MagicMock()

    @pytest.mark.asyncio
    async def test_retrieval_task_conversion(self):
        """Test that retrieval task is converted to tag"""
        data = {
            "model": "nova-embeddings-v1",
            "task": "retrieval",
            "input": ["test input"]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        assert "metadata" in result
        assert "tags" in result["metadata"]
        assert "retrieval" in result["metadata"]["tags"]
        # Original task should be preserved
        assert result["task"] == "retrieval"

    @pytest.mark.asyncio
    async def test_retrieval_passage_task_conversion(self):
        """Test that retrieval.passage subtask is converted to tag"""
        data = {
            "model": "nova-embeddings-v1",
            "task": "retrieval.passage",
            "input": [{"text": "document to index"}]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        assert result["metadata"]["tags"] == ["retrieval.passage"]

    @pytest.mark.asyncio
    async def test_code_query_task_conversion(self):
        """Test that code.query task is converted to tag"""
        data = {
            "model": "nova-embeddings-v1",
            "task": "code.query",
            "input": [{"text": "function to parse JSON"}]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        assert result["metadata"]["tags"] == ["code.query"]

    @pytest.mark.asyncio
    async def test_text_matching_task_conversion(self):
        """Test that text-matching task is converted to tag"""
        data = {
            "model": "nova-embeddings-v1",
            "task": "text-matching",
            "input": ["text1", "text2"]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        assert result["metadata"]["tags"] == ["text-matching"]

    @pytest.mark.asyncio
    async def test_non_nova_model_passthrough(self):
        """Test that non-Nova models are not modified"""
        data = {
            "model": "text-embedding-ada-002",
            "input": ["test input"]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        # Should not add metadata
        assert "metadata" not in result or "tags" not in result.get("metadata", {})

    @pytest.mark.asyncio
    async def test_non_embedding_call_passthrough(self):
        """Test that non-embedding calls are not modified"""
        data = {
            "model": "nova-embeddings-v1",
            "messages": [{"role": "user", "content": "test"}]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="completion"
        )
        
        # Should not process non-embedding requests
        assert "metadata" not in result or "tags" not in result.get("metadata", {})

    @pytest.mark.asyncio
    async def test_preserves_existing_tags(self):
        """Test that existing tags are preserved"""
        data = {
            "model": "nova-embeddings-v1",
            "task": "retrieval",
            "metadata": {
                "tags": ["custom-tag"]
            },
            "input": ["test"]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        # Should preserve existing tag and add task tag
        assert "custom-tag" in result["metadata"]["tags"]
        assert "retrieval" in result["metadata"]["tags"]
        assert len(result["metadata"]["tags"]) == 2

    @pytest.mark.asyncio
    async def test_no_task_parameter(self):
        """Test behavior when task parameter is missing"""
        data = {
            "model": "nova-embeddings-v1",
            "input": ["test input"]
        }
        
        result = await self.hook.async_pre_call_hook(
            user_api_key_dict=self.user_api_key_dict,
            cache=self.cache,
            data=data,
            call_type="embeddings"
        )
        
        # Should not error, just log warning and return unchanged
        assert result == data


def test_hook_singleton_exists():
    """Test that the singleton instance is importable"""
    from litellm.proxy.hooks.nova_task_routing import nova_task_router
    
    assert nova_task_router is not None
    assert isinstance(nova_task_router, NovaTaskRoutingHook)

