"""Job-Description Alignment Agent -- responsibility: score how well an
interview answer's language aligns with a specific job description's stated
requirements, for role-specific and company-context interview modes.
Deterministic keyword-overlap arithmetic, the same pattern as
ATSBenchmarkAgent -- no model call needed for this kind of scoring, and it
keeps the "missing company context" CARE route (retrieval-style: grounding
the evaluation in the actual JD text rather than a generic rubric) cheap and
auditable.
"""

import re
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.agents.resume_evidence_agent import _significant_terms


class JDAlignmentInput(AgentInput):
    transcript: str
    job_description_text: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class JDAlignmentOutput(AgentOutput):
    role_alignment_score: float = 0.0
    matched_terms: list[str] = Field(default_factory=list)
    missing_context_warning: bool = False


class JDAlignmentAgent(Agent[JDAlignmentInput, JDAlignmentOutput]):
    name = "jd_alignment"
    prompt_version = "jd-alignment-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = ["job_description_text"]
    output_cls = JDAlignmentOutput

    def run(self, agent_input: JDAlignmentInput) -> JDAlignmentOutput:
        if not agent_input.job_description_text.strip():
            return JDAlignmentOutput(
                confidence=0.0,
                evidence_ids=[],
                reasoning_summary="No job description is attached to this interview session.",
                inference_type="deterministic_calculation",
                role_alignment_score=0.0,
                matched_terms=[],
                missing_context_warning=True,
            )

        jd_terms = _significant_terms(agent_input.job_description_text, limit=20)
        transcript_lower = agent_input.transcript.lower()
        matched = [t for t in jd_terms if re.search(rf"\b{re.escape(t)}\b", transcript_lower)]
        score = round(len(matched) / len(jd_terms), 4) if jd_terms else 0.0
        confidence = round(min(0.5 + 0.02 * len(jd_terms), 0.9), 4)

        return JDAlignmentOutput(
            confidence=confidence,
            evidence_ids=agent_input.evidence_ids,
            reasoning_summary=(
                f"Answer used {len(matched)}/{len(jd_terms)} key term(s) from the job description "
                f"({', '.join(matched) or 'none'})."
            ),
            inference_type="deterministic_calculation",
            role_alignment_score=score,
            matched_terms=matched,
            missing_context_warning=False,
        )
