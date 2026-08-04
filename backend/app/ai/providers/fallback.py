import logging

from app.ai.providers.errors import ProviderError
from app.ai.schemas import ChatResult, StructuredChatRequest

logger = logging.getLogger(__name__)


class FallbackChatProvider:
    """Wraps a live provider with a deterministic fallback.

    Graceful provider failure (Prompt 2 requirement): if the primary
    provider raises `ProviderError` (timeout, invalid structured output
    after repair retries, upstream error), this degrades to the fallback
    provider rather than propagating an error up through an agent into the
    student-facing flow. The result is tagged `is_fallback=True` so callers
    and the Trust Center can distinguish a degraded response from a normal
    one.
    """

    def __init__(self, primary, fallback) -> None:
        self._primary = primary
        self._fallback = fallback
        self.name = f"{primary.name}+fallback:{fallback.name}"

    def complete_structured(self, request: StructuredChatRequest) -> ChatResult:
        try:
            return self._primary.complete_structured(request)
        except ProviderError as exc:
            logger.warning(
                "Provider %s failed for task_type=%s, degrading to %s: %s",
                self._primary.name,
                request.task_type,
                self._fallback.name,
                exc,
            )
            result = self._fallback.complete_structured(request)
            return result.model_copy(update={"is_fallback": True})
