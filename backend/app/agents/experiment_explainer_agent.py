"""Experiment Explainer Agent -- responsibility: turn the simulation
engine's already-computed component deltas into encouraging, readable prose.
This agent NEVER computes a number -- every score, delta, and confidence it
receives was produced by `app/simulation/engine.py` before this agent ever
runs, and its structured input schema has no field the agent could use to
invent a new one. The deterministic fallback (no live key) restates the same
numbers plainly, proving the fallback path never fabricates content either
(Prompt 3: "Allow an AI agent to explain simulation output, but not secretly
create the numeric output").
"""

import json
from typing import ClassVar

from pydantic import BaseModel, Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "experiment-explainer-v1"


class ComponentChangeSummary(BaseModel):
    component_type: str
    current_score: float | None
    simulated_score: float
    delta: float


class ExperimentExplainerInput(AgentInput):
    component_changes: list[ComponentChangeSummary]
    overall_current_score: float | None
    overall_simulated_score: float
    overall_delta: float | None
    assumptions: list[str] = Field(default_factory=list)


class ExperimentExplainerOutput(AgentOutput):
    narrative: str = ""


def _deterministic_explanation(request: StructuredChatRequest) -> dict:
    data = json.loads(request.messages[-1].content)
    lines = []
    for change in data["component_changes"]:
        label = change["component_type"].replace("_readiness", "").replace("_", " ")
        direction = "improve" if change["delta"] >= 0 else "decline"
        lines.append(f"{label.title()} is estimated to {direction} by {abs(change['delta']):.2f}")
    narrative = "; ".join(lines) + "." if lines else "No components were affected by this scenario."
    if data["overall_delta"] is not None:
        direction = "up" if data["overall_delta"] >= 0 else "down"
        narrative += f" Overall readiness moves {direction} by {abs(data['overall_delta']):.2f}."
    return {"narrative": narrative}


class ExperimentExplainerAgent(Agent[ExperimentExplainerInput, ExperimentExplainerOutput]):
    name = "experiment_explainer"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 8.0
    allowed_tools: ClassVar[list[str]] = ["simulation_result"]
    output_cls = ExperimentExplainerOutput

    def run(self, agent_input: ExperimentExplainerInput) -> ExperimentExplainerOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="experiment_explanation",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content=(
                        "Restate the already-computed scenario simulation numbers in plain, encouraging language. "
                        "Do not invent, adjust, or estimate any number yourself -- only describe the numbers given."
                    ),
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="ExperimentExplainerOutput",
            deterministic_fn=_deterministic_explanation,
        )
        result = provider.complete_structured(request)
        return ExperimentExplainerOutput(
            confidence=0.6 if result.is_fallback else 0.85,
            evidence_ids=[],
            reasoning_summary=result.parsed["narrative"],
            inference_type=result.inference_type,
            narrative=result.parsed["narrative"],
        )
