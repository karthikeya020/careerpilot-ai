from typing import Protocol

from app.ai.schemas import (
    ChatResult,
    EmbeddingResult,
    RerankCandidate,
    RerankedItem,
    StructuredChatRequest,
)


class ChatProvider(Protocol):
    name: str

    def complete_structured(self, request: StructuredChatRequest) -> ChatResult: ...


class EmbeddingProvider(Protocol):
    name: str
    dims: int

    def embed(self, texts: list[str]) -> list[EmbeddingResult]: ...


class RerankerProvider(Protocol):
    name: str

    def rerank(self, query: str, candidates: list[RerankCandidate]) -> list[RerankedItem]: ...
