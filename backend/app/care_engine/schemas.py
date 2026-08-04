from typing import Literal

from pydantic import BaseModel, Field

CareRoute = Literal[
    "deterministic",
    "single_agent",
    "graphrag_agent",
    "multi_agent",
    "critic_reflection",
    "human_review",
]

TaskRisk = Literal["low", "medium", "high"]
StudentImpact = Literal["low", "medium", "high"]


class RoutingFactors(BaseModel):
    """Mutable state threaded through one CARE decision loop. Each step
    executor is allowed to update the fields it is responsible for
    (retrieval sets `retrieval_confidence`/`evidence_count`/
    `retrieval_attempted`; a single/multi-agent pass sets `agent_confidence`/
    `agent_disagreement`) so the next `decide_route` call sees fresh state --
    this is what makes the loop match the CARE flowchart in
    docs/05_CARE_ENGINE_SPEC.md instead of routing once and stopping."""

    task_type: str
    task_risk: TaskRisk = "low"
    student_impact_level: StudentImpact = "low"

    evidence_count: int = 0
    evidence_quality: float = 0.5
    evidence_conflict: bool = False

    retrieval_attempted: bool = False
    retrieval_confidence: float | None = None

    agent_confidence: float | None = None
    agent_disagreement: float | None = None
    multi_agent_attempted: bool = False

    provider_available: bool = True
    cost_budget_ok: bool = True
    latency_budget_ok: bool = True

    deterministic_eligible: bool = False
    min_evidence_for_confidence: int = 2


class CareResult(BaseModel):
    route: CareRoute
    route_path: list[CareRoute] = Field(default_factory=list)
    confidence: float
    evidence_ids: list[str] = Field(default_factory=list)
    agents_invoked: list[str] = Field(default_factory=list)
    agreement: float | None = None
    reasoning_summary: str
    requires_human_review: bool
    retrieval_used: bool = False
    reflection_used: bool = False
    cost_usd: float = 0.0
    latency_ms: float = 0.0
    output: dict = Field(default_factory=dict)
