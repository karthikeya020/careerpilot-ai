"""CARE routing policy. Implements the table in docs/05_CARE_ENGINE_SPEC.md:

| Condition                                          | Route                    |
|------------------------------------------------------|-------------------------|
| Confidence >= 0.80 and evidence sufficient            | Single specialist        |
| Confidence 0.55-0.79 or evidence incomplete           | Hybrid GraphRAG retrieval |
| Conflicting evidence or confidence < 0.55             | Multi-agent council       |
| Agent disagreement > 0.20                             | Critic/reflection pass    |
| Final confidence < 0.50 or high-risk ambiguity         | Human-review recommendation |

Plus the Prompt 2 addition: a pure deterministic calculation never invokes
an agent at all. `decide_route` is a pure function (no DB, no provider call)
so it is exhaustively unit-testable -- see tests/test_care_policy.py.
"""

from app.care_engine.schemas import CareRoute, RoutingFactors

POLICY_VERSION = "care-policy-v1"

SINGLE_AGENT_CONFIDENCE_THRESHOLD = 0.80
MULTI_AGENT_CONFIDENCE_THRESHOLD = 0.55
DISAGREEMENT_THRESHOLD = 0.20
HUMAN_REVIEW_CONFIDENCE_THRESHOLD = 0.50
HIGH_RISK_CONFIDENCE_THRESHOLD = 0.65


def _evidence_sufficient(factors: RoutingFactors) -> bool:
    return factors.evidence_count >= factors.min_evidence_for_confidence and factors.evidence_quality >= 0.5


def decide_route(factors: RoutingFactors) -> CareRoute:
    if factors.deterministic_eligible and factors.task_risk == "low" and not factors.evidence_conflict:
        return "deterministic"

    if not _evidence_sufficient(factors) and not factors.retrieval_attempted:
        return "graphrag_agent"

    # Retrieval either wasn't needed or already ran -- decide on
    # confidence/conflict using whatever evidence is now available.
    effective_confidence = factors.agent_confidence
    if effective_confidence is None:
        effective_confidence = factors.retrieval_confidence if factors.retrieval_confidence is not None else 0.0

    if factors.agent_disagreement is not None and factors.agent_disagreement > DISAGREEMENT_THRESHOLD:
        return "critic_reflection"

    should_escalate_to_multi_agent = (
        not factors.multi_agent_attempted
        and (factors.evidence_conflict or effective_confidence < MULTI_AGENT_CONFIDENCE_THRESHOLD)
        and (factors.agent_confidence is not None or factors.evidence_conflict)
    )
    if should_escalate_to_multi_agent:
        # A single-agent pass already ran (or evidence actively conflicts)
        # and confidence is still low -- escalate once to a multi-agent
        # council. If the council itself is still low afterward
        # (multi_agent_attempted=True), fall through instead of looping back
        # here -- that's the "persistently low confidence" case that should
        # reach human review below.
        return "multi_agent"

    is_high_risk_ambiguous = factors.task_risk == "high" and effective_confidence < HIGH_RISK_CONFIDENCE_THRESHOLD
    should_recommend_human_review = (
        (effective_confidence < HUMAN_REVIEW_CONFIDENCE_THRESHOLD or is_high_risk_ambiguous)
        and (factors.agent_confidence is not None or factors.retrieval_attempted)
    )
    if should_recommend_human_review:
        # Only recommend human review after at least one real attempt
        # produced a low-confidence result -- never on the very first
        # decision before any evidence-gathering happened.
        return "human_review"

    if effective_confidence >= SINGLE_AGENT_CONFIDENCE_THRESHOLD or _evidence_sufficient(factors):
        return "single_agent"

    return "multi_agent"


def reasoning_summary_for_route(route: CareRoute, factors: RoutingFactors) -> str:
    if route == "deterministic":
        return f"Task type '{factors.task_type}' is a pure calculation; no model call was needed."
    if route == "graphrag_agent":
        return (
            f"Evidence was insufficient ({factors.evidence_count} item(s), "
            f"quality {factors.evidence_quality:.2f}) -- retrieving related context before reasoning."
        )
    if route == "single_agent":
        return "Evidence was sufficient and initial confidence was high enough for a single specialist."
    if route == "multi_agent":
        reason = "conflicting evidence" if factors.evidence_conflict else "low single-agent confidence"
        return f"Escalated to a multi-agent council due to {reason}."
    if route == "critic_reflection":
        return (
            f"Agent disagreement ({factors.agent_disagreement:.2f}) exceeded the "
            f"{DISAGREEMENT_THRESHOLD:.2f} threshold -- running a critic/reflection pass."
        )
    return "Confidence remained low after reasoning and retrieval -- recommending human review."
