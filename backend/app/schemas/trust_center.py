import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AgentRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    agent_name: str
    prompt_version: str
    confidence: float
    evidence_citations: list[str]
    inference_type: str
    status: str
    latency_ms: float
    created_at: datetime
    # Raw agent output (e.g. the GraphRAG agent's `graph_source` field --
    # "neo4j" or "relational_fallback" -- so the Trust Center can label which
    # data path actually produced a root-cause result).
    output_payload: dict


class CareExecutionSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    task_type: str
    route: str
    confidence: float
    agents_invoked: list[str]
    retrieval_used: bool
    reflection_used: bool
    requires_human_review: bool
    final_status: str
    created_at: datetime


class CareExecutionDetailOut(CareExecutionSummaryOut):
    request_summary: str
    input_evidence_ids: list[str]
    routing_factors: dict
    reasoning_summary: str
    agreement: float | None
    cost_usd: float
    latency_ms: float
    policy_version: str
    agent_runs: list[AgentRunOut]


class ComponentDiffOut(BaseModel):
    component_type: str
    previous_score: float | None
    current_score: float | None
    delta: float | None
    evidence_count: int
    evidence_ids: list[str]
    explanation: str


class TwinChangeExplanationOut(BaseModel):
    snapshot_id: uuid.UUID
    version: int
    overall_score: float | None
    overall_confidence: float | None
    score_delta: float | None
    change_summary: str
    formula_version: str
    component_diffs: list[ComponentDiffOut]
