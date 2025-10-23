"""
LiteLLM Responses API transformation for Hosted RemodlAI.

This mirrors the OpenAI Responses API implementation while swapping in
Hosted RemodlAI specific authentication and endpoint handling. RemodlAI
provides a fully OpenAI-compatible surface area (responses, streaming,
function calling, etc.) for both Nova native models and any custom model
hosted on the cluster.
"""

from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    cast,
    get_type_hints,
)

import httpx
from openai.types.responses import ResponseReasoningItem
from pydantic import BaseModel

import litellm
from litellm._logging import verbose_logger
from litellm.litellm_core_utils.llm_response_utils.convert_dict_to_response import (
    _safe_convert_created_field,
)
from litellm.llms.base_llm.chat.transformation import BaseLLMException
from litellm.llms.base_llm.responses.transformation import BaseResponsesAPIConfig
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


class RemodlAIResponsesAPIError(BaseLLMException):
    def __init__(
        self,
        status_code: int,
        message: str,
        headers: Optional[Union[dict, httpx.Headers]] = None,
        request: Optional[httpx.Request] = None,
        response: Optional[httpx.Response] = None,
        body: Optional[dict] = None,
    ):
        super().__init__(
            status_code=status_code,
            message=message,
            headers=headers,
            request=request,
            response=response,
            body=body,
        )


class RemodlAIResponsesAPIConfig(BaseResponsesAPIConfig):
    @property
    def custom_llm_provider(self) -> LlmProviders:
        return LlmProviders.REMODL_AI

    def get_supported_openai_params(self, model: str) -> list:
        """
        Hosted RemodlAI supports the full OpenAI Responses API surface.
        """
        supported_params = get_type_hints(ResponsesAPIRequestParams).keys()
        return list(
            set(
                [
                    "input",
                    "model",
                    "extra_headers",
                    "extra_query",
                    "extra_body",
                    "timeout",
                ]
                + list(supported_params)
            )
        )

    def map_openai_params(
        self,
        response_api_optional_params: ResponsesAPIOptionalRequestParams,
        model: str,
        drop_params: bool,
    ) -> Dict:
        """No mapping required – Nova consumes OpenAI-spec parameters directly."""
        return dict(response_api_optional_params)

    def transform_responses_api_request(
        self,
        model: str,
        input: Union[str, ResponseInputParam],
        response_api_optional_request_params: Dict,
        litellm_params: GenericLiteLLMParams,
        headers: dict,
    ) -> Dict:
        """No transformation required – just validate the input payload."""
        input = self._validate_input_param(input)
        final_request_params = dict(
            ResponsesAPIRequestParams(
                model=model, input=input, **response_api_optional_request_params
            )
        )
        return final_request_params

    def _validate_input_param(
        self, input: Union[str, ResponseInputParam]
    ) -> Union[str, ResponseInputParam]:
        """
        Ensure any pydantic inputs are converted to plain dicts to keep the
        wire payload OpenAI-compatible.
        """
        if isinstance(input, list):
            validated_input = []
            for item in input:
                if isinstance(item, BaseModel):
                    validated_input.append(item.model_dump(exclude_none=True))
                elif isinstance(item, dict):
                    verbose_logger.debug(f"Handling reasoning item: {item}")
                    if item.get("type") == "reasoning":
                        dict_item = cast(Dict[str, Any], item)
                        filtered_item = self._handle_reasoning_item(dict_item)
                    else:
                        filtered_item = cast(Dict[str, Any], item)
                    validated_input.append(filtered_item)
                else:
                    validated_input.append(item)
            return validated_input  # type: ignore[return-value]
        return input

    def _handle_reasoning_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter out None values on reasoning items using OpenAI's model so that
        Hosted RemodlAI receives the exact schema it expects.
        """
        if item.get("type") == "reasoning":
            try:
                item_data = dict(item)
                if "id" not in item_data:
                    item_data["id"] = f"rs_{hash(str(item_data))}"
                if "summary" not in item_data:
                    reasoning_content = item_data.get("reasoning_content", "")
                    item_data["summary"] = (
                        reasoning_content[:100] + "..."
                        if len(reasoning_content) > 100
                        else reasoning_content
                    )

                reasoning_item = ResponseReasoningItem(**item_data)
                return reasoning_item.model_dump(exclude_none=True)
            except Exception as e:
                verbose_logger.debug(
                    f"Failed to create ResponseReasoningItem, falling back to manual filtering: {e}"
                )
                return {
                    k: v
                    for k, v in item.items()
                    if v is not None
                    or k not in {"status", "content", "encrypted_content"}
                }
        return item

    def transform_response_api_response(
        self,
        model: str,
        raw_response: httpx.Response,
        logging_obj: LiteLLMLoggingObj,
    ) -> ResponsesAPIResponse:
        """Pass through the OpenAI-formatted response from Hosted RemodlAI."""
        try:
            logging_obj.post_call(
                original_response=raw_response.text,
                additional_args={"complete_input_dict": {}},
            )
            raw_response_json = raw_response.json()
            raw_response_json["created_at"] = _safe_convert_created_field(
                raw_response_json["created_at"]
            )
        except Exception:
            raise RemodlAIResponsesAPIError(
                message=raw_response.text,
                status_code=raw_response.status_code,
                headers=raw_response.headers,
                response=raw_response,
            )
        try:
            return ResponsesAPIResponse(**raw_response_json)
        except Exception:
            verbose_logger.debug(
                f"Error constructing ResponsesAPIResponse: {raw_response_json}, using model_construct"
            )
            return ResponsesAPIResponse.model_construct(**raw_response_json)

    def validate_environment(
        self, headers: dict, model: str, litellm_params: Optional[GenericLiteLLMParams]
    ) -> dict:
        litellm_params = litellm_params or GenericLiteLLMParams()
        api_key = (
            getattr(litellm_params, "api_key", None)
            or get_secret_str("REMODL_AI_API_KEY")
            or "fake-api-key"
        )
        headers.update(
            {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }
        )
        return headers

    def get_complete_url(
        self,
        api_base: Optional[str],
        litellm_params: dict,
    ) -> str:
        """
        Hosted RemodlAI exposes an OpenAI-compatible `/v1/responses` endpoint.
        """
        api_base = (
            api_base
            or litellm.api_base
            or get_secret_str("REMODL_AI_API_BASE")
        )

        if api_base is None:
            raise ValueError(
                "REMODL_AI_API_BASE is not set. Please configure the API base."
            )

        api_base = api_base.rstrip("/")
        if api_base.endswith("/responses"):
            return api_base
        if api_base.endswith("/v1"):
            return f"{api_base}/responses"
        if api_base.endswith("/v1/"):
            return f"{api_base}responses"
        return f"{api_base}/v1/responses"

    def transform_streaming_response(
        self,
        model: str,
        parsed_chunk: dict,
        logging_obj: LiteLLMLoggingObj,
    ) -> ResponsesAPIStreamingResponse:
        """
        Convert Nova streaming chunks into strongly-typed Responses API events.
        """
        verbose_logger.debug("Raw Hosted RemodlAI chunk=%s", parsed_chunk)
        event_type = str(parsed_chunk.get("type"))
        event_pydantic_model = RemodlAIResponsesAPIConfig.get_event_model_class(
            event_type=event_type
        )
        return event_pydantic_model(**parsed_chunk)

    @staticmethod
    def get_event_model_class(event_type: str) -> Any:
        """
        Select the appropriate streaming event model for the provided chunk.
        """
        event_models = {
            ResponsesAPIStreamEvents.RESPONSE_CREATED: ResponseCreatedEvent,
            ResponsesAPIStreamEvents.RESPONSE_IN_PROGRESS: ResponseInProgressEvent,
            ResponsesAPIStreamEvents.RESPONSE_COMPLETED: ResponseCompletedEvent,
            ResponsesAPIStreamEvents.RESPONSE_FAILED: ResponseFailedEvent,
            ResponsesAPIStreamEvents.RESPONSE_INCOMPLETE: ResponseIncompleteEvent,
            ResponsesAPIStreamEvents.OUTPUT_ITEM_ADDED: OutputItemAddedEvent,
            ResponsesAPIStreamEvents.OUTPUT_ITEM_DONE: OutputItemDoneEvent,
            ResponsesAPIStreamEvents.CONTENT_PART_ADDED: ContentPartAddedEvent,
            ResponsesAPIStreamEvents.CONTENT_PART_DONE: ContentPartDoneEvent,
            ResponsesAPIStreamEvents.OUTPUT_TEXT_DELTA: OutputTextDeltaEvent,
            ResponsesAPIStreamEvents.OUTPUT_TEXT_ANNOTATION_ADDED: OutputTextAnnotationAddedEvent,
            ResponsesAPIStreamEvents.OUTPUT_TEXT_DONE: OutputTextDoneEvent,
            ResponsesAPIStreamEvents.REFUSAL_DELTA: RefusalDeltaEvent,
            ResponsesAPIStreamEvents.REFUSAL_DONE: RefusalDoneEvent,
            ResponsesAPIStreamEvents.FUNCTION_CALL_ARGUMENTS_DELTA: FunctionCallArgumentsDeltaEvent,
            ResponsesAPIStreamEvents.FUNCTION_CALL_ARGUMENTS_DONE: FunctionCallArgumentsDoneEvent,
            ResponsesAPIStreamEvents.FILE_SEARCH_CALL_IN_PROGRESS: FileSearchCallInProgressEvent,
            ResponsesAPIStreamEvents.FILE_SEARCH_CALL_SEARCHING: FileSearchCallSearchingEvent,
            ResponsesAPIStreamEvents.FILE_SEARCH_CALL_COMPLETED: FileSearchCallCompletedEvent,
            ResponsesAPIStreamEvents.WEB_SEARCH_CALL_IN_PROGRESS: WebSearchCallInProgressEvent,
            ResponsesAPIStreamEvents.WEB_SEARCH_CALL_SEARCHING: WebSearchCallSearchingEvent,
            ResponsesAPIStreamEvents.WEB_SEARCH_CALL_COMPLETED: WebSearchCallCompletedEvent,
            ResponsesAPIStreamEvents.MCP_LIST_TOOLS_IN_PROGRESS: MCPListToolsInProgressEvent,
            ResponsesAPIStreamEvents.MCP_LIST_TOOLS_COMPLETED: MCPListToolsCompletedEvent,
            ResponsesAPIStreamEvents.MCP_LIST_TOOLS_FAILED: MCPListToolsFailedEvent,
            ResponsesAPIStreamEvents.MCP_CALL_IN_PROGRESS: MCPCallInProgressEvent,
            ResponsesAPIStreamEvents.MCP_CALL_ARGUMENTS_DELTA: MCPCallArgumentsDeltaEvent,
            ResponsesAPIStreamEvents.MCP_CALL_ARGUMENTS_DONE: MCPCallArgumentsDoneEvent,
            ResponsesAPIStreamEvents.MCP_CALL_COMPLETED: MCPCallCompletedEvent,
            ResponsesAPIStreamEvents.MCP_CALL_FAILED: MCPCallFailedEvent,
            ResponsesAPIStreamEvents.IMAGE_GENERATION_PARTIAL_IMAGE: ImageGenerationPartialImageEvent,
            ResponsesAPIStreamEvents.ERROR: ErrorEvent,
        }

        model_class = event_models.get(cast(ResponsesAPIStreamEvents, event_type))
        if not model_class:
            return GenericEvent
        return model_class

    def should_fake_stream(
        self,
        model: Optional[str],
        stream: Optional[bool],
        custom_llm_provider: Optional[str] = None,
    ) -> bool:
        """
        Hosted RemodlAI clusters natively stream responses, including custom
        models. If metadata is missing, default to real streaming rather than
        faking chunks.
        """
        if stream is not True:
            return False
        if model is not None:
            try:
                supports_stream = litellm.utils.supports_native_streaming(
                    model=model,
                    custom_llm_provider=custom_llm_provider
                    or self.custom_llm_provider.value,
                )
                if supports_stream is False:
                    # Nova still streams even if model metadata is missing
                    verbose_logger.debug(
                        "Fallback to native streaming for Hosted RemodlAI model=%s",
                        model,
                    )
                    return False
            except Exception as e:
                verbose_logger.debug(
                    "Error checking native streaming for Hosted RemodlAI (%s). Defaulting to native streaming.",
                    e,
                )
        return False

    #########################################################
    ########## DELETE RESPONSE API TRANSFORMATION ##############
    #########################################################
    def transform_delete_response_api_request(
        self,
        response_id: str,
        api_base: str,
        litellm_params: GenericLiteLLMParams,
        headers: dict,
    ) -> Tuple[str, Dict]:
        url = f"{api_base}/{response_id}"
        data: Dict = {}
        return url, data

    def transform_delete_response_api_response(
        self,
        raw_response: httpx.Response,
        logging_obj: LiteLLMLoggingObj,
    ) -> DeleteResponseResult:
        try:
            raw_response_json = raw_response.json()
        except Exception:
            raise RemodlAIResponsesAPIError(
                message=raw_response.text,
                status_code=raw_response.status_code,
                headers=raw_response.headers,
                response=raw_response,
            )
        return DeleteResponseResult(**raw_response_json)

    #########################################################
    ########## GET RESPONSE API TRANSFORMATION ###############
    #########################################################
    def transform_get_response_api_request(
        self,
        response_id: str,
        api_base: str,
        litellm_params: GenericLiteLLMParams,
        headers: dict,
    ) -> Tuple[str, Dict]:
        url = f"{api_base}/{response_id}"
        data: Dict = {}
        return url, data

    def transform_get_response_api_response(
        self,
        raw_response: httpx.Response,
        logging_obj: LiteLLMLoggingObj,
    ) -> ResponsesAPIResponse:
        try:
            raw_response_json = raw_response.json()
        except Exception:
            raise RemodlAIResponsesAPIError(
                message=raw_response.text,
                status_code=raw_response.status_code,
                headers=raw_response.headers,
                response=raw_response,
            )
        return ResponsesAPIResponse(**raw_response_json)

    #########################################################
    ########## LIST INPUT ITEMS TRANSFORMATION #############
    #########################################################
    def transform_list_input_items_request(
        self,
        response_id: str,
        api_base: str,
        litellm_params: GenericLiteLLMParams,
        headers: dict,
        after: Optional[str] = None,
        before: Optional[str] = None,
        include: Optional[List[str]] = None,
        limit: int = 20,
        order: Literal["asc", "desc"] = "desc",
    ) -> Tuple[str, Dict]:
        url = f"{api_base}/{response_id}/input_items"
        params: Dict[str, Any] = {}
        if after is not None:
            params["after"] = after
        if before is not None:
            params["before"] = before
        if include:
            params["include"] = ",".join(include)
        if limit is not None:
            params["limit"] = limit
        if order is not None:
            params["order"] = order
        return url, params

    def transform_list_input_items_response(
        self,
        raw_response: httpx.Response,
        logging_obj: LiteLLMLoggingObj,
    ) -> Dict:
        try:
            return raw_response.json()
        except Exception:
            raise RemodlAIResponsesAPIError(
                message=raw_response.text,
                status_code=raw_response.status_code,
                headers=raw_response.headers,
                response=raw_response,
            )

    #########################################################
    ########## CANCEL RESPONSE API TRANSFORMATION ##########
    #########################################################
    def transform_cancel_response_api_request(
        self,
        response_id: str,
        api_base: str,
        litellm_params: GenericLiteLLMParams,
        headers: dict,
    ) -> Tuple[str, Dict]:
        url = f"{api_base}/{response_id}/cancel"
        data: Dict = {}
        return url, data

    def transform_cancel_response_api_response(
        self,
        raw_response: httpx.Response,
        logging_obj: LiteLLMLoggingObj,
    ) -> ResponsesAPIResponse:
        try:
            raw_response_json = raw_response.json()
        except Exception:
            raise RemodlAIResponsesAPIError(
                message=raw_response.text,
                status_code=raw_response.status_code,
                headers=raw_response.headers,
                response=raw_response,
            )
        return ResponsesAPIResponse(**raw_response_json)

    #########################################################
    ########## ERROR HANDLING ################################
    #########################################################
    def get_error_class(
        self,
        error_message: str,
        status_code: int,
        headers: Union[dict, httpx.Headers],
    ) -> BaseLLMException:
        return RemodlAIResponsesAPIError(
            status_code=status_code,
            message=error_message,
            headers=headers,
        )

    def get_stripped_model_name(self, model: str) -> str:
        """
        Align model identifiers with OpenAI naming by removing the `responses/`
        prefix that Nova allows for convenience.
        """
        if "responses/" in model:
            model = model.replace("responses/", "")
        return model
