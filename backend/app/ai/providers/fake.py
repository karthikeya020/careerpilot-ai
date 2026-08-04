"""Deterministic provider used in every test and as the default when no
live API key is configured.

`FakeChatProvider` does not attempt to simulate free-form natural-language
generation -- that would be dishonest labeling. Instead, each caller passes
a `deterministic_fn` on the request that computes the structured output
directly from the input (a real, inspectable, reproducible calculation).
The provider's job is uniform plumbing: run the function, measure fake
latency, estimate token counts from text length for cost/telemetry
consistency, and tag the result's provenance correctly.
"""

import time

from app.ai.providers.errors import ProviderError
from app.ai.schemas import ChatResult, InferenceType, StructuredChatRequest


def _estimate_tokens(text: str) -> int:
    # ~4 chars/token, matches common tokenizer heuristics closely enough
    # for demo-mode cost/latency telemetry (not billed, never exact).
    return max(1, len(text) // 4)


class FakeChatProvider:
    name = "fake-deterministic"
    model = "fake-deterministic-v1"

    def complete_structured(self, request: StructuredChatRequest) -> ChatResult:
        if request.deterministic_fn is None:
            raise ProviderError(
                f"FakeChatProvider requires a deterministic_fn for task_type={request.task_type!r}"
            )
        start = time.perf_counter()
        try:
            outcome = request.deterministic_fn(request)
        except Exception as exc:
            raise ProviderError(f"deterministic_fn failed for {request.task_type!r}: {exc}") from exc
        latency_ms = (time.perf_counter() - start) * 1000

        inference_type: InferenceType = "deterministic_calculation"
        if isinstance(outcome, tuple):
            parsed, inference_type = outcome
        else:
            parsed = outcome

        input_text = "\n".join(m.content for m in request.messages)
        return ChatResult(
            parsed=parsed,
            raw_text=str(parsed),
            provider_name=self.name,
            model=self.model,
            prompt_version=request.prompt_version,
            inference_type=inference_type,
            input_tokens=_estimate_tokens(input_text),
            output_tokens=_estimate_tokens(str(parsed)),
            latency_ms=round(latency_ms, 3),
            cost_usd=0.0,
            is_fallback=True,
        )
