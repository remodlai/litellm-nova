"""
Transformation logic for Hosted Lexiq Nova embeddings

Supports Nova Embeddings V1 multivector, multimodal embedding model with:
- Token-level (multivector) or pooled embeddings
- Multimodal support (text + images)
- Task-specific adapters (retrieval, text-matching, code)
- Matryoshka dimensions
"""

from typing import Any, Dict, List, Optional, Union

import httpx

from litellm.llms.base_llm.chat.transformation import BaseLLMException
from litellm.llms.base_llm.embedding.transformation import BaseEmbeddingConfig
from litellm.secret_managers.main import get_secret_str
from litellm.types.llms.openai import AllMessageValues


class HostedLexiqNovaEmbeddingError(BaseLLMException):
    def __init__(
        self,
        status_code: int,
        message: str,
        headers: Optional[Union[dict, httpx.Headers]] = None,
    ):
        super().__init__(status_code=status_code, message=message, headers=headers)


class HostedLexiqNovaEmbeddingConfig(BaseEmbeddingConfig):
    """
    Configuration for Hosted Lexiq Nova embedding models.
    
    Extends OpenAI embedding interface with Nova-specific parameters:
    - task: Required top-level task (retrieval, text-matching, code)
    - return_multivector: True for token-level embeddings, False for pooled
    - instructions: Custom instructions for the embedding prompt
    - adapter: Override adapter per input item
    - image: URL, base64, or bytes for multimodal embeddings
    - image_embeds: Precomputed vision embeddings
    """

    def __init__(self) -> None:
        super().__init__()

    def get_supported_openai_params(self, model: str) -> List[str]:
        """
        Nova supports standard OpenAI embedding params plus custom ones
        """
        return [
            "input",
            "model",
            "encoding_format",
            "dimensions",
            "user",
            "timeout",
            # Nova-specific params
            "task",
            "return_multivector",
            "instructions",
            "adapter",
            "image",
            "image_embeds",
        ]

    def map_openai_params(
        self,
        non_default_params: dict,
        optional_params: dict,
        model: str,
        drop_params: bool,
    ) -> dict:
        """
        Pass through Nova-specific parameters to the API
        """
        # Nova-specific parameters that should be passed through
        nova_params = [
            "task",
            "return_multivector",
            "instructions",
            "adapter",
            "image",
            "image_embeds",
        ]
        
        for param in nova_params:
            if param in non_default_params:
                optional_params[param] = non_default_params.pop(param)
        
        # Handle standard OpenAI params
        return super().map_openai_params(
            non_default_params, optional_params, model, drop_params
        )

    def validate_environment(
        self,
        headers: dict,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        api_key: Optional[str] = None,
    ) -> dict:
        """
        Set up authentication headers for Nova embeddings
        """
        if api_key is None:
            api_key = get_secret_str("HOSTED_LEXIQ_NOVA_API_KEY") or "fake-api-key"

        headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"
        
        return headers

    def get_complete_url(
        self,
        api_base: Optional[str],
        model: str,
        optional_params: dict,
        stream: Optional[bool] = None,
    ) -> str:
        """
        Returns the complete URL for Nova embeddings endpoint
        """
        api_base = api_base or get_secret_str("HOSTED_LEXIQ_NOVA_API_BASE")
        
        if api_base is None:
            raise ValueError(
                "HOSTED_LEXIQ_NOVA_API_BASE is not set. Please set the environment variable."
            )

        # Remove trailing slashes
        api_base = api_base.rstrip("/")
        
        # Add the /v1/embeddings endpoint
        if not api_base.endswith("/v1/embeddings"):
            api_base = f"{api_base}/v1/embeddings"
        
        return api_base

    def get_error_class(
        self,
        error_message: str,
        status_code: int,
        headers: Union[dict, httpx.Headers],
    ) -> BaseLLMException:
        return HostedLexiqNovaEmbeddingError(
            message=error_message, status_code=status_code, headers=headers
        )

