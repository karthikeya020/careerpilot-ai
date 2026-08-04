"""Live cloud-provider adapter. Only instantiated by the registry when
`settings.primary_llm_api_key` is set (see app/ai/registry.py) -- never
imported or exercised by the test suite, so `anthropic` being unreachable or
unconfigured never breaks CI or the demo.

Approximate per-1K-token USD pricing, used only for telemetry/cost tracking
in the Trust Center and research instrumentation -- not a billing source of
truth.
"""

import json
import time

from app.ai.providers.errors import ProviderError
from app.ai.schemas import ChatResult, StructuredChatRequest

_PRICE_PER_1K_TOKENS_USD = {
    "input": 0.003,
    "output": 0.015,
}
_MAX_ATTEMPTS = 2


def _strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped
        if stripped.endswith("```"):
            stripped = stripped.rsplit("```", 1)[0]
    return stripped.strip()


class AnthropicChatProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, timeout_seconds: float = 30.0) -> None:
        self._model = model
        self._timeout_seconds = timeout_seconds
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - only hit if dependency missing at runtime
            raise ProviderError("anthropic package is not installed") from exc
        self._client = anthropic.Anthropic(api_key=api_key, timeout=timeout_seconds)

    def complete_structured(self, request: StructuredChatRequest) -> ChatResult:
        system = next((m.content for m in request.messages if m.role == "system"), "")
        turns: list[dict] = [
            {"role": m.role, "content": m.content} for m in request.messages if m.role != "system"
        ]
        json_instruction = (
            "Respond with a single valid JSON object only -- no markdown code fences, "
            "no commentary before or after the JSON."
        )
        last_error: Exception | None = None
        start = time.perf_counter()

        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                response = self._client.messages.create(
                    model=self._model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    system=f"{system}\n\n{json_instruction}".strip(),
                    # Plain dicts match the SDK's MessageParam TypedDict shape at runtime.
                    messages=turns,  # type: ignore[arg-type]
                )
                raw_text = "".join(
                    getattr(block, "text", "") for block in response.content if getattr(block, "type", None) == "text"
                )
                parsed = json.loads(_strip_code_fence(raw_text))
                latency_ms = (time.perf_counter() - start) * 1000
                input_tokens = getattr(response.usage, "input_tokens", 0)
                output_tokens = getattr(response.usage, "output_tokens", 0)
                cost_usd = (
                    input_tokens / 1000 * _PRICE_PER_1K_TOKENS_USD["input"]
                    + output_tokens / 1000 * _PRICE_PER_1K_TOKENS_USD["output"]
                )
                return ChatResult(
                    parsed=parsed,
                    raw_text=raw_text,
                    provider_name=self.name,
                    model=self._model,
                    prompt_version=request.prompt_version,
                    inference_type="model_inference",
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    latency_ms=round(latency_ms, 3),
                    cost_usd=round(cost_usd, 6),
                    is_fallback=False,
                )
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                turns.append({"role": "assistant", "content": raw_text if "raw_text" in locals() else ""})
                turns.append(
                    {
                        "role": "user",
                        "content": f"That was not valid JSON ({exc}). Respond again with valid JSON only.",
                    }
                )
                continue
            except Exception as exc:
                last_error = exc
                break

        raise ProviderError(
            f"Anthropic structured completion failed for task_type={request.task_type!r} "
            f"after {_MAX_ATTEMPTS} attempt(s): {last_error}"
        )
