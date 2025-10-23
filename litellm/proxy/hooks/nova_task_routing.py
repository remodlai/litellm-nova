"""
Nova Embeddings Task-Based Routing Hook

Converts Nova's 'task' parameter to LiteLLM's tag-based routing.

Usage:
1. Add to proxy_config.yaml:
   litellm_settings:
     callbacks: litellm.proxy.hooks.nova_task_routing.nova_task_router

2. Configure model_list with task tags:
   model_list:
     - model_name: nova-embeddings-v1
       litellm_params:
         model: remodlai/nova-embeddings-retrieval
         tags: ["retrieval", "retrieval.query", "retrieval.passage"]
     - model_name: nova-embeddings-v1
       litellm_params:
         model: remodlai/nova-embeddings-text-matching
         tags: ["text-matching"]
     - model_name: nova-embeddings-v1
       litellm_params:
         model: remodlai/nova-embeddings-code
         tags: ["code", "code.query", "code.passage"]

3. Enable tag filtering:
   router_settings:
     enable_tag_filtering: True
"""

from typing import TYPE_CHECKING, Any, Literal, Optional

from litellm._logging import verbose_logger
from litellm.integrations.custom_logger import CustomLogger

if TYPE_CHECKING:
    from litellm.proxy.proxy_server import DualCache, UserAPIKeyAuth
else:
    DualCache = Any
    UserAPIKeyAuth = Any


class NovaTaskRoutingHook(CustomLogger):
    """
    Converts Nova Embeddings 'task' parameter to tag-based routing.
    
    When a request includes:
      {"model": "nova-embeddings-v1", "task": "retrieval.passage", ...}
    
    This hook transforms it to:
      {"model": "nova-embeddings-v1", "metadata": {"tags": ["retrieval.passage"]}, ...}
    
    The existing tag router then selects the deployment with matching tags.
    """

    def __init__(self):
        super().__init__()
        verbose_logger.debug("NovaTaskRoutingHook initialized")

    async def async_pre_call_hook(
        self,
        user_api_key_dict: UserAPIKeyAuth,
        cache: DualCache,
        data: dict,
        call_type: Literal[
            "completion",
            "text_completion",
            "embeddings",
            "image_generation",
            "moderation",
            "audio_transcription",
        ],
    ):
        """
        Pre-call hook that converts 'task' to 'tags' for Nova embeddings.
        
        Only activates for:
        - call_type == "embeddings"
        - model contains "nova-embeddings"
        """
        
        # Only process embedding requests
        if call_type != "embeddings":
            return data
        
        model = data.get("model", "")
        
        # Only process Nova embedding models
        if "nova-embeddings" not in model:
            return data
        
        # Extract the task parameter
        task = data.get("task")
        
        if not task:
            verbose_logger.warning(
                "Nova embedding request without 'task' parameter. "
                "Defaulting to untagged routing. Model: %s",
                model
            )
            return data
        
        verbose_logger.debug(
            "NovaTaskRoutingHook: Converting task '%s' to tag for model '%s'",
            task,
            model
        )
        
        # Initialize metadata if not present
        if "metadata" not in data:
            data["metadata"] = {}
        
        # Initialize tags if not present
        if "tags" not in data["metadata"]:
            data["metadata"]["tags"] = []
        
        # Add task to tags (if not already present)
        if task not in data["metadata"]["tags"]:
            data["metadata"]["tags"].append(task)
        
        verbose_logger.debug(
            "NovaTaskRoutingHook: Updated metadata tags: %s",
            data["metadata"]["tags"]
        )
        
        return data


# Create singleton instance for import
nova_task_router = NovaTaskRoutingHook()

