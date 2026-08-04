"""Single place business logic asks for a provider. Swapping/adding a
provider means editing this file only -- no caller imports a provider SDK
type directly (Constitution rule 9).
"""

from functools import lru_cache

from app.ai.embeddings.hashing import HashingEmbeddingProvider
from app.ai.providers.fake import FakeChatProvider
from app.ai.providers.fallback import FallbackChatProvider
from app.ai.rerank.simple import SimpleReranker
from app.core.config import get_settings


@lru_cache
def get_chat_provider():
    settings = get_settings()
    fake = FakeChatProvider()
    if not settings.primary_llm_api_key:
        return fake
    from app.ai.providers.anthropic_provider import AnthropicChatProvider

    live = AnthropicChatProvider(api_key=settings.primary_llm_api_key, model=settings.primary_llm_model)
    return FallbackChatProvider(primary=live, fallback=fake)


@lru_cache
def get_embedding_provider() -> HashingEmbeddingProvider:
    return HashingEmbeddingProvider()


@lru_cache
def get_reranker() -> SimpleReranker:
    return SimpleReranker()
