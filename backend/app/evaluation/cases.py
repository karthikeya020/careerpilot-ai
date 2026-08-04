"""Curated evaluation dataset for Experiment A (docs/06_EVALUATION_PLAN.md):
comparing a fixed single-agent baseline, a fixed multi-agent baseline, and
CARE's adaptive routing. `expected_route` is a synthetic rubric label (a
human-reviewed dataset is a Phase 3 item -- see PHASE_2_COMPLETION_REPORT
limitations) used only to compute an agreement metric between variants,
covering easy, ambiguous, contradictory, and low-evidence cases per the
evaluation plan's dataset strategy.
"""

from typing import Any, TypedDict


class EvaluationCase(TypedDict):
    case_id: str
    task_type: str
    factors: dict[str, Any]
    expected_route: str


EVALUATION_CASES: list[EvaluationCase] = [
    {
        "case_id": "easy-sufficient-evidence",
        "task_type": "resume_insight",
        "factors": {"evidence_count": 5, "evidence_quality": 0.9, "agent_confidence": 0.9},
        "expected_route": "single_agent",
    },
    {
        "case_id": "missing-context",
        "task_type": "root_cause_analysis",
        "factors": {"evidence_count": 0, "evidence_quality": 0.2},
        "expected_route": "graphrag_agent",
    },
    {
        "case_id": "conflicting-evidence",
        "task_type": "jd_match_review",
        "factors": {"evidence_count": 5, "evidence_quality": 0.8, "evidence_conflict": True, "agent_confidence": 0.6},
        "expected_route": "multi_agent",
    },
    {
        "case_id": "ambiguous-low-single-agent-confidence",
        "task_type": "career_coach_synthesis",
        "factors": {"evidence_count": 4, "evidence_quality": 0.7, "agent_confidence": 0.4},
        "expected_route": "multi_agent",
    },
    {
        "case_id": "high-disagreement-after-council",
        "task_type": "career_coach_synthesis",
        "factors": {
            "evidence_count": 4, "evidence_quality": 0.7, "agent_confidence": 0.6, "agent_disagreement": 0.35,
        },
        "expected_route": "critic_reflection",
    },
    {
        "case_id": "persistently-low-confidence",
        "task_type": "ambiguous_case",
        "factors": {
            "evidence_count": 5, "evidence_quality": 0.8, "agent_confidence": 0.3,
            "retrieval_attempted": True, "multi_agent_attempted": True,
        },
        "expected_route": "human_review",
    },
    {
        "case_id": "high-risk-ambiguity",
        "task_type": "high_stakes_case",
        "factors": {
            "task_risk": "high", "evidence_count": 5, "evidence_quality": 0.8, "agent_confidence": 0.6,
            "retrieval_attempted": True,
        },
        "expected_route": "human_review",
    },
    {
        "case_id": "pure-deterministic-calculation",
        "task_type": "score_aggregation",
        "factors": {"deterministic_eligible": True, "task_risk": "low"},
        "expected_route": "deterministic",
    },
]
