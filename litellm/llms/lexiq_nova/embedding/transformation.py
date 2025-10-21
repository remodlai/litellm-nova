"""
Embedding transformation for Lexiq Nova (local SDK).

Use hosted_lexiq_nova for production deployments.
"""

from ...hosted_lexiq_nova.embedding.transformation import (
    HostedLexiqNovaEmbeddingConfig,
)


class LexiqNovaEmbeddingConfig(HostedLexiqNovaEmbeddingConfig):
    """
    Lexiq Nova SDK supports the same embedding params as hosted_lexiq_nova.
    """

    pass

