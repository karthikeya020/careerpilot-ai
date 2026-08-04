"""ATS Benchmark Agent -- responsibility: score resume-to-JD keyword
coverage the way an applicant-tracking-system keyword filter would. This is
intentionally pure arithmetic over already-computed matched/partial/missing
skill sets (see app/services/job_description_service.py::compute_match) --
no model call, no LLM cost, fully deterministic and instant.
"""

from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput


class ATSBenchmarkInput(AgentInput):
    matched_skills: list[str]
    partial_skills: list[str]
    missing_skills: list[str]
    evidence_ids: list[str] = Field(default_factory=list)


class ATSBenchmarkOutput(AgentOutput):
    ats_score: float = 0.0
    missing_keywords: list[str] = Field(default_factory=list)


class ATSBenchmarkAgent(Agent[ATSBenchmarkInput, ATSBenchmarkOutput]):
    name = "ats_benchmark"
    prompt_version = "ats-benchmark-v1"
    timeout_seconds = 1.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = ATSBenchmarkOutput

    def run(self, agent_input: ATSBenchmarkInput) -> ATSBenchmarkOutput:
        total = len(agent_input.matched_skills) + len(agent_input.partial_skills) + len(agent_input.missing_skills)
        if total == 0:
            return ATSBenchmarkOutput(
                confidence=0.0,
                evidence_ids=agent_input.evidence_ids,
                reasoning_summary="No job requirements available to benchmark against.",
                inference_type="deterministic_calculation",
                ats_score=0.0,
                missing_keywords=[],
            )
        weighted = len(agent_input.matched_skills) + 0.5 * len(agent_input.partial_skills)
        ats_score = round(weighted / total, 4)
        confidence = round(min(0.6 + 0.1 * min(total, 4), 0.95), 4)
        return ATSBenchmarkOutput(
            confidence=confidence,
            evidence_ids=agent_input.evidence_ids,
            reasoning_summary=(
                f"{len(agent_input.matched_skills)} matched, {len(agent_input.partial_skills)} partial, "
                f"{len(agent_input.missing_skills)} missing out of {total} requirement(s) -- ATS score {ats_score:.2f}."
            ),
            inference_type="deterministic_calculation",
            ats_score=ats_score,
            missing_keywords=agent_input.missing_skills,
        )
