"""Resume Intelligence Agent -- responsibility: synthesize a short,
evidence-grounded strengths/gaps summary from an already-parsed resume
(parsing itself stays in app/services/resume_service.py, which is
deterministic and unchanged from Phase 1). This is the one place a
generative model can add real value -- turning a list of matched skills and
detected sections into readable natural language -- so it goes through the
provider abstraction; with no live key configured it falls back to a
deterministic template, never a fabricated claim.
"""

import json
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.ai.registry import get_chat_provider
from app.ai.schemas import ChatMessage, StructuredChatRequest

PROMPT_VERSION = "resume-intelligence-v1"
_EXPECTED_SECTIONS = {"skills", "experience", "projects", "education"}


class ResumeIntelligenceInput(AgentInput):
    student_name: str
    skills_found: list[str]
    sections_found: list[str]
    evidence_ids: list[str] = Field(default_factory=list)


class ResumeIntelligenceOutput(AgentOutput):
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    summary: str = ""


def _deterministic_resume_insight(request: StructuredChatRequest) -> dict:
    payload = request.messages[-1].content
    data = json.loads(payload)
    skills = data["skills_found"]
    sections = {s.lower() for s in data["sections_found"]}
    strengths = [f"Demonstrated skill: {s}" for s in skills[:5]]
    missing_sections = sorted(_EXPECTED_SECTIONS - sections)
    gaps = [f"No '{s}' section detected" for s in missing_sections]
    summary = (
        f"{data['student_name']}'s resume shows {len(skills)} matched skill(s) across "
        f"{len(sections)} detected section(s)."
    )
    return {"strengths": strengths, "gaps": gaps, "summary": summary}


class ResumeIntelligenceAgent(Agent[ResumeIntelligenceInput, ResumeIntelligenceOutput]):
    name = "resume_intelligence"
    prompt_version = PROMPT_VERSION
    timeout_seconds = 8.0
    allowed_tools: ClassVar[list[str]] = ["resume_parser_output"]
    output_cls = ResumeIntelligenceOutput

    def run(self, agent_input: ResumeIntelligenceInput) -> ResumeIntelligenceOutput:
        provider = get_chat_provider()
        request = StructuredChatRequest(
            task_type="resume_insight",
            prompt_version=self.prompt_version,
            messages=[
                ChatMessage(role="system", content="Summarize resume strengths and gaps concisely and factually."),
                ChatMessage(role="user", content=json.dumps(agent_input.model_dump())),
            ],
            response_schema_name="ResumeIntelligenceOutput",
            deterministic_fn=_deterministic_resume_insight,
        )
        result = provider.complete_structured(request)
        coverage = min(len(agent_input.skills_found) / 5, 1.0)
        confidence = round(0.5 + 0.4 * coverage, 4)
        return ResumeIntelligenceOutput(
            confidence=confidence,
            evidence_ids=agent_input.evidence_ids,
            reasoning_summary=result.parsed["summary"],
            inference_type=result.inference_type,
            strengths=result.parsed["strengths"],
            gaps=result.parsed["gaps"],
            summary=result.parsed["summary"],
        )
