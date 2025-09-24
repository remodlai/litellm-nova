"""
Translates from OpenAI's `/v1/chat/completions` to the Nova sdk `llm.generate`. 

NOT RECOMMENDED FOR PRODUCTION USE. Use `hosted_nova/` instead.
"""

from ...hosted_nova.chat.transformation import HostedNOVAChatConfig


class NovaConfig(HostedNOVAChatConfig):
    """
    Nova SDK supports the same OpenAI params as hosted_nova.
    """

    pass
