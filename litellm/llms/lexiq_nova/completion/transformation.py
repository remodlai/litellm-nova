"""
Translates from OpenAI's `/v1/chat/completions` to the Lexiq Nova SDK `llm.generate`. 

NOT RECOMMENDED FOR PRODUCTION USE. Use `hosted_lexiq_nova/` instead.
"""

from ...hosted_lexiq_nova.chat.transformation import HostedLexiqNovaChatConfig


class LexiqNovaConfig(HostedLexiqNovaChatConfig):
    """
    Lexiq Nova SDK supports the same OpenAI params as hosted_lexiq_nova.
    """

    pass

