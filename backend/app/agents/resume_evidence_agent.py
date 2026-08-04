"""Resume Evidence Agent -- responsibility: check a claim made during an
interview answer against the student's actual uploaded resume text, and
return one of the respectful classifications Prompt 3 requires. Deterministic
keyword-grounded matching, not a model judgment call -- claim-checking is
exactly the kind of decision that should be auditable and reproducible
rather than a free-form model opinion, and it must never accuse the student
of dishonesty (Constitution rule 7: no lie detection).

v1 limitation, documented rather than hidden: this heuristic can detect
"supported" / "partially supported" / "not currently supported" /
"insufficient evidence" from keyword co-occurrence, but does not attempt
negation-aware contradiction detection -- `EVIDENCE_CHECK_CONTRADICTED`
exists in the schema for a future, more careful pass and is never emitted by
this implementation.
"""

import re
from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput
from app.models.interview import (
    EVIDENCE_CHECK_INSUFFICIENT,
    EVIDENCE_CHECK_NOT_SUPPORTED,
    EVIDENCE_CHECK_PARTIAL,
    EVIDENCE_CHECK_SUPPORTED,
)

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "your", "you", "i",
    "was", "were", "have", "has", "had", "that", "this", "would", "could", "can", "my", "me",
    "when", "where", "which", "there", "their", "then", "than", "also", "into", "about",
}


def _significant_terms(text: str, limit: int = 10) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.]{3,}", text.lower())
    seen: dict[str, int] = {}
    order: list[str] = []
    for w in words:
        if w in _STOPWORDS:
            continue
        if w not in seen:
            order.append(w)
        seen[w] = seen.get(w, 0) + 1
    order.sort(key=lambda w: seen[w], reverse=True)
    return order[:limit]


_EXPLANATIONS = {
    EVIDENCE_CHECK_SUPPORTED: "This claim is well supported by details already present in the uploaded resume.",
    EVIDENCE_CHECK_PARTIAL: (
        "This claim is only partially reflected in the uploaded resume. Consider adding supporting "
        "details to your resume or expanding on the specifics in your answer."
    ),
    EVIDENCE_CHECK_NOT_SUPPORTED: (
        "This claim is not currently supported by the uploaded resume or project evidence. "
        "Consider adding supporting details or revising the answer."
    ),
    EVIDENCE_CHECK_INSUFFICIENT: "No resume has been uploaded yet, so this claim cannot be checked against evidence.",
}


class ResumeEvidenceCheckInput(AgentInput):
    claim_text: str
    resume_text: str = ""
    evidence_ids: list[str] = Field(default_factory=list)


class ResumeEvidenceCheckOutput(AgentOutput):
    classification: str = EVIDENCE_CHECK_INSUFFICIENT
    matched_terms: list[str] = Field(default_factory=list)
    explanation_text: str = ""


class ResumeEvidenceAgent(Agent[ResumeEvidenceCheckInput, ResumeEvidenceCheckOutput]):
    name = "resume_evidence"
    prompt_version = "resume-evidence-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = ["resume_text"]
    output_cls = ResumeEvidenceCheckOutput

    def run(self, agent_input: ResumeEvidenceCheckInput) -> ResumeEvidenceCheckOutput:
        if not agent_input.resume_text.strip():
            return ResumeEvidenceCheckOutput(
                confidence=0.2,
                evidence_ids=[],
                reasoning_summary=_EXPLANATIONS[EVIDENCE_CHECK_INSUFFICIENT],
                inference_type="deterministic_calculation",
                classification=EVIDENCE_CHECK_INSUFFICIENT,
                matched_terms=[],
                explanation_text=_EXPLANATIONS[EVIDENCE_CHECK_INSUFFICIENT],
            )

        claim_terms = _significant_terms(agent_input.claim_text)
        resume_lower = agent_input.resume_text.lower()
        matched = [t for t in claim_terms if t in resume_lower]

        if len(matched) >= 2:
            classification = EVIDENCE_CHECK_SUPPORTED
        elif len(matched) == 1:
            classification = EVIDENCE_CHECK_PARTIAL
        else:
            classification = EVIDENCE_CHECK_NOT_SUPPORTED

        confidence = round(min(0.5 + 0.15 * len(claim_terms), 0.85), 4) if claim_terms else 0.3
        explanation = _EXPLANATIONS[classification]
        return ResumeEvidenceCheckOutput(
            confidence=confidence,
            evidence_ids=agent_input.evidence_ids,
            reasoning_summary=f"{explanation} (matched terms: {', '.join(matched) or 'none'})",
            inference_type="deterministic_calculation",
            classification=classification,
            matched_terms=matched,
            explanation_text=explanation,
        )
