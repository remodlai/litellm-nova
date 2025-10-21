"""
Responses API transformation for Lexiq Nova.

This follows the same pattern as vllm -> hosted_vllm.
Use hosted_lexiq_nova for production deployments.
"""

from ...hosted_lexiq_nova.responses.transformation import (
    HostedLexiqNovaResponsesAPIConfig,
)


class LexiqNovaResponsesAPIConfig(HostedLexiqNovaResponsesAPIConfig):
    """
    Lexiq Nova SDK supports the same OpenAI Responses API params as hosted_lexiq_nova.
    """

    pass

