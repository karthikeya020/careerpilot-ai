class ProviderError(Exception):
    """Raised by any ChatProvider/EmbeddingProvider/RerankerProvider on
    unrecoverable failure (timeout exhausted, invalid structured output
    after repair retry, upstream error). Agents catch this and degrade to
    their documented failure behavior -- providers never silently return
    fabricated data.
    """
