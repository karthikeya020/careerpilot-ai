import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AllocationRequest(BaseModel):
    skill_name: str
    activity_type: str
    hours: float = Field(gt=0, le=200)


class StartExperimentRequest(BaseModel):
    name: str
    allocations: list[AllocationRequest]
    target_role_id: uuid.UUID | None = None
    time_horizon_days: int = Field(default=30, gt=0, le=365)


class ComponentChangeOut(BaseModel):
    component_type: str
    current_score: float | None
    simulated_score: float
    delta: float
    confidence: float
    uncertainty: float
    assumptions: list[str] = Field(default_factory=list)
    evidence_used: list[str] = Field(default_factory=list)


class ExperimentResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    engine_version: str
    baseline_snapshot_id: uuid.UUID | None
    current_overall_score: float | None
    simulated_overall_score: float | None
    overall_score_delta: float | None
    overall_confidence: float
    overall_uncertainty: float
    component_changes: list[ComponentChangeOut]
    assumptions: list[str]
    evidence_used: list[str]
    explanation: str
    disclaimer: str
    created_at: datetime


class ExperimentScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    target_role_id: uuid.UUID | None
    time_horizon_days: int
    allocations: list[dict]
    created_at: datetime
    result: ExperimentResultOut | None = None
