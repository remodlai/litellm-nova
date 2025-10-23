"""
Transformation logic for Hosted RemodlAI embeddings

Nova Embeddings V1 is based on Jina Embeddings V4 with added functionality:
- Runtime instruction tuning (Nova-specific)
- Task-specific adapters: retrieval, text-matching, code (Nova-specific)
- Token-level (multivector) or pooled embeddings (Nova-specific)
- Multimodal support: text + images (from Jina V4)
- Matryoshka dimensions (from Jina V4)
"""

import types
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import httpx

from litellm import LlmProviders
from litellm.llms.base_llm.chat.transformation import BaseLLMException
from litellm.llms.base_llm.embedding.transformation import BaseEmbeddingConfig
from litellm.litellm_core_utils.litellm_logging import Logging as LiteLLMLoggingObj
from litellm.secret_managers.main import get_secret_str
from litellm.types.llms.openai import AllEmbeddingInputValues, AllMessageValues
from litellm.types.utils import EmbeddingResponse
from litellm.utils import is_base64_encoded


class RemodlAIEmbeddingError(BaseLLMException):
    def __init__(
        self,
        status_code: int,
        message: str,
        headers: Optional[Union[dict, httpx.Headers]] = None,
    ):
        super().__init__(status_code=status_code, message=message, headers=headers)


class RemodlAIEmbeddingConfig(BaseEmbeddingConfig):
    """
    Configuration for Hosted RemodlAI embedding models.
    
    Based on Jina Embeddings V4 with Nova-specific enhancements:
    
    Jina V4 Features (inherited):
    - dimensions: Matryoshka truncation
    - Multimodal: text + base64 images
    
    Nova-Specific Features (added):
    - instructions: Runtime instruction tuning for domain adaptation
    - task: Task-specific adapters (retrieval, text-matching, code)
    - return_multivector: Token-level (128d) vs pooled (up to 2048d)
    - adapter: Per-item adapter override
    - image: Enhanced multimodal (URL, base64, bytes)
    - image_embeds: Precomputed vision embeddings
    """

    def __init__(self) -> None:
        locals_ = locals().copy()
        for key, value in locals_.items():
            if key != "self" and value is not None:
                setattr(self.__class__, key, value)

    @classmethod
    def get_config(cls):
        return {
            k: v
            for k, v in cls.__dict__.items()
            if not k.startswith("__")
            and not isinstance(
                v,
                (
                    types.FunctionType,
                    types.BuiltinFunctionType,
                    classmethod,
                    staticmethod,
                ),
            )
            and v is not None
        }

    def get_supported_openai_params(self, model: str) -> List[str]:
        """
        Nova supports Jina V4 params + Nova-specific extensions
        
        Jina V4: dimensions
        Nova adds: instructions, task, return_multivector, adapter, image, image_embeds
        """
        return [
            "input",
            "model",
            "encoding_format",
            "dimensions",  # From Jina V4 - matryoshka truncation
            "user",
            "timeout",
            # Nova-specific params
            "task",  # retrieval, text-matching, code
            "return_multivector",  # true=token-level, false=pooled
            "instructions",  # Runtime instruction tuning
            "adapter",  # Per-item adapter override
            "image",  # Multimodal support
            "image_embeds",  # Precomputed vision embeddings
        ]

    def map_openai_params(
        self,
        non_default_params: dict,
        optional_params: dict,
        model: str,
        drop_params: bool,
    ) -> dict:
        """
        Map parameters for Nova Embeddings V1
        
        Handles both Jina V4 base params and Nova-specific extensions
        """
        # Jina V4 param: dimensions (matryoshka)
        if "dimensions" in non_default_params:
            optional_params["dimensions"] = non_default_params.pop("dimensions")
        
        # Nova-specific parameters
        nova_params = [
            "task",  # Required: retrieval, text-matching, code
            "return_multivector",  # Token-level vs pooled
            "instructions",  # Runtime instruction tuning
            "adapter",  # Per-item adapter override
            "image",  # Multimodal support
            "image_embeds",  # Precomputed embeddings
        ]
        
        for param in nova_params:
            if param in non_default_params:
                optional_params[param] = non_default_params.pop(param)
        
        return optional_params

    def validate_environment(
        self,
        headers: dict,
        model: str,
        messages: List[AllMessageValues],
        optional_params: dict,
        litellm_params: dict,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ) -> dict:
        """
        Set up authentication headers for Nova embeddings (aligned with Jina pattern)
        """
        default_headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            default_headers["Authorization"] = f"Bearer {api_key}"
        headers = {**default_headers, **headers}
        return headers

    def _get_openai_compatible_provider_info(
        self,
        api_base: Optional[str],
        api_key: Optional[str],
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Returns provider info aligned with Jina's pattern
        
        Returns:
            Tuple[str, Optional[str], Optional[str]]:
                - custom_llm_provider: str
                - api_base: str
                - dynamic_api_key: str
        """
        api_base = (
            api_base
            or get_secret_str("HOSTED_LEXIQ_NOVA_API_BASE")
            or get_secret_str("LEXIQ_NOVA_API_BASE")
        )
        dynamic_api_key = (
            api_key
            or get_secret_str("HOSTED_LEXIQ_NOVA_API_KEY")
            or get_secret_str("LEXIQ_NOVA_API_KEY")
            or "fake-api-key"  # Nova doesn't require API key for local deployments
        )
        return LlmProviders.HOSTED_LEXIQ_NOVA.value, api_base, dynamic_api_key

    def get_complete_url(
        self,
        api_base: Optional[str],
        api_key: Optional[str],
        model: str,
        optional_params: dict,
        litellm_params: dict,
        stream: Optional[bool] = None,
    ) -> str:
        """
        Returns the complete URL for Nova embeddings endpoint
        """
        return (
            f"{api_base}/embeddings"
            if api_base
            else "https://api.lexiq-nova.com/v1/embeddings"
        )

    def transform_embedding_request(
        self,
        model: str,
        input: AllEmbeddingInputValues,
        optional_params: dict,
        headers: dict,
    ) -> dict:
        """
        Transform embedding request for Nova Embeddings V1
        
        Handles:
        - Jina V4 base64 image format (inherited)
        - Nova-specific task/adapter/instructions parameters (added)
        - Standard text inputs
        """
        data = {"model": model, **optional_params}
        
        # Handle input transformation (following Jina V4 pattern for images)
        input = cast(List[str], input) if isinstance(input, List) else [input]
        
        # Check if any inputs are base64-encoded images (Jina V4 compatibility)
        if any((is_base64_encoded(x) if isinstance(x, str) else False for x in input)):
            transformed_input = []
            for value in input:
                if isinstance(value, str):
                    if is_base64_encoded(value):
                        # Extract base64 data (remove data URI prefix if present)
                        img_data = value.split(",")[1] if "," in value else value
                        transformed_input.append({"image": img_data})
                    else:
                        transformed_input.append({"text": value})
                elif isinstance(value, dict):
                    # Already in Nova format (e.g., {"text": "...", "image": "..."})
                    transformed_input.append(value)
            data["input"] = transformed_input
        else:
            data["input"] = input
        
        return data

    def transform_embedding_response(
        self,
        model: str,
        raw_response: httpx.Response,
        model_response: EmbeddingResponse,
        logging_obj: LiteLLMLoggingObj,
        api_key: Optional[str],
        request_data: dict,
        optional_params: dict,
        litellm_params: dict,
    ) -> EmbeddingResponse:
        """
        Transform Nova embedding response (aligned with Jina V4 pattern)
        """
        response_json = raw_response.json()
        
        ## LOGGING
        logging_obj.post_call(
            input=request_data.get("input"),
            api_key=api_key,
            additional_args={"complete_input_dict": request_data},
            original_response=response_json,
        )
        
        return EmbeddingResponse(**response_json)

    def get_error_class(
        self,
        error_message: str,
        status_code: int,
        headers: Union[dict, httpx.Headers],
    ) -> BaseLLMException:
        return RemodlAIEmbeddingError(
            message=error_message, status_code=status_code, headers=headers
        )

