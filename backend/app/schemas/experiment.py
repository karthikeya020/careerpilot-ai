import uuid
from datetime import date, datetime

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


class SensitivityFactorOut(BaseModel):
    factor: str
    label: str
    swing: float


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
    sensitivity: list[SensitivityFactorOut] = Field(default_factory=list)
    waste_notes: list[str] = Field(default_factory=list)
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


class TargetPlanRequest(BaseModel):
    target_component: str
    target_score: float = Field(gt=0, le=1)
    candidate_skills: list[str] = Field(min_length=1, max_length=10)
    weekly_hours: float = Field(default=10, gt=0, le=80)
    deadline: date | None = None
    activity_type: str = "practice_problems"


class AllocationPlanItemOut(BaseModel):
    skill_name: str
    activity_type: str
    hours: float
    order_rank: int
    scheduling_reason: str | None = None


class CalendarWeekOut(BaseModel):
    week_number: int
    start_date: str
    items: list[dict]
    total_hours: float


class CalendarPlanOut(BaseModel):
    weeks: list[CalendarWeekOut]
    weekly_hours_budget: float
    total_hours: float
    weeks_needed: int
    deadline: str | None
    fits_deadline: bool | None
    feasibility_note: str | None


class MarginalGainPointOut(BaseModel):
    hours: float
    marginal_gain: float
    cumulative_gain: float


class TargetPlanOut(BaseModel):
    engine_version: str
    target_component: str
    target_score: float
    baseline_score: float | None
    reached_target: bool
    plan: list[AllocationPlanItemOut]
    total_hours: float
    weeks_to_complete: int | None
    assumptions: list[str]
    disclaimer: str
    calendar: CalendarPlanOut
    marginal_gain_curve: list[MarginalGainPointOut]


class PredictionAccuracyOut(BaseModel):
    status: str
    predicted_delta: float | None = None
    actual_delta: float | None = None
    absolute_error: float | None = None
    days_elapsed: int | None = None
    baseline_snapshot_version: int | None = None
    current_snapshot_version: int | None = None
    message: str
