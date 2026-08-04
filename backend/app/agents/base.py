"""Shared agent contract.

Every specialist agent below is a subclass of `Agent[InputT, OutputT]` with:
- a typed Pydantic input and output (output always extends `AgentOutput`,
  which carries confidence, evidence citations, a reasoning summary, and an
  explicit inference_type -- Prompt 2's "distinguish extracted facts /
  model inferences / deterministic calculations / user claims" requirement)
- `name`, `prompt_version`, `timeout_seconds`, `allowed_tools` class attrs
- defined failure behavior: `safe_run` never raises -- on any exception it
  returns a zero-confidence, `status="failed"` output instead, which is why
  every Output subclass must give a default to every field beyond the
  AgentOutput base (documented per-agent).

No agent writes to the Career Twin. Agents only produce typed outputs;
`app/career_twin/scoring.py::recompute_twin` is the only place evidence
turns into a stored score (Constitution rule 1).
"""

import time
from abc import ABC, abstractmethod
from typing import ClassVar, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

from app.ai.schemas import InferenceType

AgentStatus = Literal["completed", "failed"]


class AgentInput(BaseModel):
    pass


class AgentOutput(BaseModel):
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)
    reasoning_summary: str
    inference_type: InferenceType
    status: AgentStatus = "completed"


InputT = TypeVar("InputT", bound=AgentInput)
OutputT = TypeVar("OutputT", bound=AgentOutput)


class Agent(ABC, Generic[InputT, OutputT]):
    name: ClassVar[str]
    prompt_version: ClassVar[str]
    timeout_seconds: ClassVar[float] = 10.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls: ClassVar[type[AgentOutput]]

    @abstractmethod
    def run(self, agent_input: InputT) -> OutputT: ...

    def safe_run(self, agent_input: InputT) -> tuple[OutputT, float]:
        """Returns (output, latency_ms). Never raises."""
        start = time.perf_counter()
        try:
            output = self.run(agent_input)
        except Exception as exc:
            output = self.output_cls(
                confidence=0.0,
                evidence_ids=[],
                reasoning_summary=f"{self.name} failed: {exc}",
                inference_type="deterministic_calculation",
                status="failed",
            )  # type: ignore[assignment]
        latency_ms = (time.perf_counter() - start) * 1000
        return output, latency_ms
