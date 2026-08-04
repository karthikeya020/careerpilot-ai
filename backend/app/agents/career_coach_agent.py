"""Career Coach Agent -- responsibility: turn a root-cause path and the
current priority readiness component into a short, encouraging,
student-facing explanation and a recommended focus area. This is a
synthesis task where a real model adds genuine value (natural, readable
phrasing); the deterministic fallback still produces a correct, if plainer,
explanation from the same inputs -- never fabricated content, just less
polished prose.
"""

import json
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "career-coach-v1"


class CareerCoachInput(AgentInput):
    student_name: str
    priority_component: str
    root_cause_summary: str
    concept_name: str
    evidence_ids: list[str] = Field(default_factory=list)


class CareerCoachOutput(AgentOutput):
    explanation: str = ""
    recommended_focus: str = ""


def _deterministic_coach_synthesis(request: StructuredChatRequest) -> dict:
    data = json.loads(request.messages[-1].content)
    component_label = data["priority_component"].replace("_", " ")
    explanation = (
        f"{data['student_name']}, your current priority weakness is {component_label}. "
        f"{data['root_cause_summary']} Focusing on {data['concept_name']} should move this component the most."
    )
    return {"explanation": explanation, "recommended_focus": data["concept_name"]}


class CareerCoachAgent(Agent[CareerCoachInput, CareerCoachOutput]):
    name = "career_coach"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 8.0
    allowed_tools: ClassVar[list[str]] = ["root_cause_result", "readiness_components"]
    output_cls = CareerCoachOutput

    def run(self, agent_input: CareerCoachInput) -> CareerCoachOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="career_coach_synthesis",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(
                    role="system",
                    content="Write a short, encouraging explanation of the student's priority weakness and what to focus on next.",
                ),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="CareerCoachOutput",
            deterministic_fn=_deterministic_coach_synthesis,
        )
        result = provider.complete_structured(request)
        return CareerCoachOutput(
            confidence=0.6 if result.is_fallback else 0.85,
            evidence_ids=agent_input.evidence_ids,
            reasoning_summary=result.parsed["explanation"],
            inference_type=result.inference_type,
            explanation=result.parsed["explanation"],
            recommended_focus=result.parsed["recommended_focus"],
        )
