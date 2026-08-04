from app.care_engine.policy import decide_route
from app.care_engine.schemas import RoutingFactors


def test_deterministic_calculation_never_invokes_an_agent():
    factors = RoutingFactors(task_type="score_aggregation", deterministic_eligible=True, task_risk="low")
    assert decide_route(factors) == "deterministic"


def test_sufficient_high_confidence_evidence_routes_to_single_agent():
    factors = RoutingFactors(
        task_type="resume_insight", evidence_count=5, evidence_quality=0.9, agent_confidence=0.9
    )
    assert decide_route(factors) == "single_agent"


def test_missing_context_routes_to_graphrag_retrieval():
    factors = RoutingFactors(task_type="root_cause_analysis", evidence_count=0, evidence_quality=0.2)
    assert decide_route(factors) == "graphrag_agent"


def test_conflicting_evidence_routes_to_multi_agent():
    factors = RoutingFactors(
        task_type="jd_match_review",
        evidence_count=5,
        evidence_quality=0.8,
        evidence_conflict=True,
        agent_confidence=0.6,
    )
    assert decide_route(factors) == "multi_agent"


def test_high_disagreement_routes_to_critic_reflection():
    factors = RoutingFactors(
        task_type="career_coach_synthesis",
        evidence_count=5,
        evidence_quality=0.8,
        agent_confidence=0.6,
        agent_disagreement=0.35,
    )
    assert decide_route(factors) == "critic_reflection"


def test_persistently_low_confidence_recommends_human_review():
    # Simulates the state *after* a multi-agent council already ran and its
    # consensus confidence is still low -- this is the "persistently low
    # confidence" case, distinct from a single agent's first low reading
    # (which should escalate to multi_agent instead, see the test above).
    factors = RoutingFactors(
        task_type="ambiguous_case",
        evidence_count=5,
        evidence_quality=0.8,
        agent_confidence=0.3,
        retrieval_attempted=True,
        multi_agent_attempted=True,
    )
    assert decide_route(factors) == "human_review"


def test_high_risk_ambiguity_recommends_human_review_even_with_moderate_confidence():
    factors = RoutingFactors(
        task_type="high_stakes_case",
        task_risk="high",
        evidence_count=5,
        evidence_quality=0.8,
        agent_confidence=0.6,
        retrieval_attempted=True,
    )
    assert decide_route(factors) == "human_review"


def test_retrieval_only_attempted_once():
    factors = RoutingFactors(
        task_type="root_cause_analysis",
        evidence_count=0,
        evidence_quality=0.2,
        retrieval_attempted=True,
        retrieval_confidence=0.3,
    )
    # Evidence is still thin after one retrieval pass -- must not loop back
    # into graphrag_agent again; low confidence with no agent pass yet
    # should fall through toward an agent route, not stall.
    assert decide_route(factors) != "graphrag_agent"
