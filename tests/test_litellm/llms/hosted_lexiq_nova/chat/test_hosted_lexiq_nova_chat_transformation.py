import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

sys.path.insert(
    0, os.path.abspath("../../../../..")
)  # Adds the parent directory to the system path

from litellm.llms.hosted_lexiq_nova.chat.transformation import HostedLexiqNovaChatConfig


def test_hosted_lexiq_nova_chat_transformation_file_url():
    config = HostedLexiqNovaChatConfig()
    video_url = "https://example.com/video.mp4"
    video_data = f"data:video/mp4;base64,{video_url}"
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "file",
                    "file": {
                        "file_data": video_data,
                    },
                }
            ],
        }
    ]
    transformed_response = config.transform_request(
        model="hosted_lexiq_nova/llama-3.1-70b-instruct",
        messages=messages,
        optional_params={},
        litellm_params={},
        headers={},
    )
    assert transformed_response["messages"] == [
        {
            "role": "user",
            "content": [{"type": "video_url", "video_url": {"url": video_data}}],
        }
    ]


def test_hosted_lexiq_nova_chat_transformation_with_audio_url():
    from litellm import completion
    from litellm.llms.custom_httpx.http_handler import HTTPHandler

    client = MagicMock()

    with patch.object(
        client.chat.completions.with_raw_response, "create", return_value=MagicMock()
    ) as mock_post:
        try:
            response = completion(
                model="hosted_lexiq_nova/llama-3.1-70b-instruct",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "audio_url",
                                "audio_url": {"url": "https://example.com/audio.mp3"},
                            },
                        ],
                    },
                ],
                client=client,
            )
        except Exception as e:
            print(f"Error: {e}")

        mock_post.assert_called_once()
        print(f"mock_post.call_args.kwargs: {mock_post.call_args.kwargs}")
        assert mock_post.call_args.kwargs["messages"] == [
            {
                "role": "user",
                "content": [
                    {
                        "type": "audio_url",
                        "audio_url": {"url": "https://example.com/audio.mp3"},
                    }
                ],
            }
        ]


def test_hosted_lexiq_nova_supports_reasoning_effort():
    config = HostedLexiqNovaChatConfig()
    supported_params = config.get_supported_openai_params(
        model="hosted_lexiq_nova/gpt-oss-120b"
    )
    assert "reasoning_effort" in supported_params
    optional_params = config.map_openai_params(
        non_default_params={"reasoning_effort": "high"},
        optional_params={},
        model="hosted_lexiq_nova/gpt-oss-120b",
        drop_params=False,
    )
    assert optional_params["reasoning_effort"] == "high"

