"""Critic / Reflection Agent -- responsibility: audit a set of prior agent
outputs for unsupported claims (nonzero confidence with no evidence
citations) and internal inconsistency, and produce an adjusted confidence.
Invoked by CARE's `critic_reflection` route when agent disagreement exceeds
the threshold (see app/care_engine/policy.py). Deterministic rule-based
audit -- a critic that itself depends on an unreliable model call would
defeat the purpose.
"""

from typing import ClassVar

from pydantic import Field

from app.agents.base import Agent, AgentInput, AgentOutput


class CriticClaim(AgentInput):
    agent_name: str
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)


class CriticInput(AgentInput):
    claims: list[CriticClaim]


class CriticOutput(AgentOutput):
    issues: list[str] = Field(default_factory=list)
    adjusted_confidence: float = 0.0
    verdict: str = "pass"


_UNSUPPORTED_CONFIDENCE_THRESHOLD = 0.5


class CriticAgent(Agent[CriticInput, CriticOutput]):
    name = "critic"
    prompt_version = "critic-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = []
    output_cls = CriticOutput

    def run(self, agent_input: CriticInput) -> CriticOutput:
        if not agent_input.claims:
            return CriticOutput(
                confidence=0.0,
                evidence_ids=[],
                reasoning_summary="No claims to audit.",
                inference_type="deterministic_calculation",
                verdict="flag",
            )

        issues = []
        for claim in agent_input.claims:
            if claim.confidence >= _UNSUPPORTED_CONFIDENCE_THRESHOLD and not claim.evidence_ids:
                issues.append(f"{claim.agent_name} reported confidence {claim.confidence:.2f} with no evidence citations.")

        mean_confidence = sum(c.confidence for c in agent_input.claims) / len(agent_input.claims)
        penalty = 0.1 * len(issues)
        adjusted_confidence = round(max(mean_confidence - penalty, 0.0), 4)
        verdict = "flag" if issues else "pass"

        return CriticOutput(
            confidence=adjusted_confidence,
            evidence_ids=[eid for claim in agent_input.claims for eid in claim.evidence_ids],
            reasoning_summary=(
                f"Audited {len(agent_input.claims)} claim(s), found {len(issues)} issue(s)."
                + (f" Issues: {'; '.join(issues)}" if issues else "")
            ),
            inference_type="deterministic_calculation",
            issues=issues,
            adjusted_confidence=adjusted_confidence,
            verdict=verdict,
        )
