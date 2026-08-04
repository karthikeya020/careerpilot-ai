"""Provider-neutral request/result shapes.

No caller in `app/agents/*` or `app/services/*` should ever import a
provider SDK type directly -- everything crosses this boundary as one of the
types below, so swapping providers never touches callers (Constitution rule
9).
"""

from typing import Any, Literal

from pydantic import BaseModel, Field

InferenceType = Literal[
    "deterministic_calculation",
    "model_inference",
    "extracted_fact",
    "user_claim",
]


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class StructuredChatRequest(BaseModel):
    task_type: str
    prompt_version: str
    messages: list[ChatMessage]
    response_schema_name: str
    max_tokens: int = 1024
    temperature: float = 0.0
    # Deterministic derivation used by FakeChatProvider (and as the repair
    # fallback if a live provider's structured output fails validation
    # twice). Not serialized -- callers pass it in-process.
    deterministic_fn: Any = Field(default=None, exclude=True)


class ChatResult(BaseModel):
    parsed: dict[str, Any]
    raw_text: str
    provider_name: str
    model: str
    prompt_version: str
    inference_type: InferenceType
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost_usd: float
    is_fallback: bool = False


class EmbeddingResult(BaseModel):
    vector: list[float]
    model: str
    dims: int
    provider_name: str
    latency_ms: float


class RerankCandidate(BaseModel):
    id: str
    text: str
    base_score: float
    metadata: dict[str, Any] = Field(default_factory=dict)


class RerankedItem(BaseModel):
    id: str
    score: float
    components: dict[str, float]
