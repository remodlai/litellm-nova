from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional, Tuple, Union

import httpx
from openai.types.responses import ResponseReasoningItem

from litellm._logging import verbose_logger
from litellm.llms.openai.responses.transformation import OpenAIResponsesAPIConfig
from litellm.secret_managers.main import get_secret_str
from litellm.types.llms.openai import *
from litellm.types.responses.main import *
from litellm.types.router import GenericLiteLLMParams
from litellm.types.utils import LlmProviders

if TYPE_CHECKING:
    from litellm.litellm_core_utils.litellm_logging import Logging as _LiteLLMLoggingObj

    LiteLLMLoggingObj = _LiteLLMLoggingObj
else:
    LiteLLMLoggingObj = Any


class HostedLexiqNovaResponsesAPIConfig(OpenAIResponsesAPIConfig):
    @property
    def custom_llm_provider(self) -> LlmProviders:
        return LlmProviders.HOSTED_LEXIQ_NOVA

    def validate_environment(
        self, headers: dict, model: str, litellm_params: Optional[GenericLiteLLMParams]
    ) -> dict:
        api_key = get_secret_str("HOSTED_LEXIQ_NOVA_API_KEY") or "fake-api-key"
        headers["Authorization"] = f"Bearer {api_key}"
        headers["Content-Type"] = "application/json"
        return headers

    def get_stripped_model_name(self, model: str) -> str:
        # if "responses/" is in the model name, remove it
        if "responses/" in model:
            model = model.replace("responses/", "")
        return model

    def get_complete_url(
        self,
        api_base: Optional[str],
        litellm_params: dict,
        model: str,
    ) -> str:
        """
        Returns the complete URL for the API request.

        For Hosted Lexiq Nova, we use the api_base directly.
        """
        api_base = api_base or get_secret_str("HOSTED_LEXIQ_NOVA_API_BASE")
        
        if api_base is None:
            raise ValueError(
                "HOSTED_LEXIQ_NOVA_API_BASE is not set. Please set the environment variable."
            )

        # Remove trailing slashes
        api_base = api_base.rstrip("/")
        
        # Add the /v1/responses endpoint
        if not api_base.endswith("/v1/responses"):
            api_base = f"{api_base}/v1/responses"
        
        return api_base

    def get_error_class(
        self,
        error_message: str,
        status_code: int,
        headers: Union[dict, httpx.Headers],
    ) -> Exception:
        from litellm.llms.hosted_lexiq_nova.chat.transformation import (
            HostedLexiqNovaChatConfig,
        )

        # Reuse the error handling from chat config since it's the same provider
        config = HostedLexiqNovaChatConfig()
        return config.get_error_class(error_message, status_code, headers)

