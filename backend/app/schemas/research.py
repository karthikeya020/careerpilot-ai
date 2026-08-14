import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RoutingExperimentOut(BaseModel):
    run_id: uuid.UUID
    dataset_name: str
    case_count: int
    agreement_rate_by_variant: dict[str, float]
    rows: list[dict]


class GraphVsVectorExperimentOut(BaseModel):
    run_id: uuid.UUID
    case_count: int
    indexed_documents: int
    graph_traversal_accuracy: float | None
    vector_only_accuracy: float | None
    rows: list[dict]
    methodology_note: str
    sample_size_warning: str


class EvaluationRunSummaryOut(BaseModel):
    id: uuid.UUID
    name: str
    dataset_name: str
    notes: str
    created_at: datetime
    result_count: int


class ReliabilityBinOut(BaseModel):
    bin_start: float
    bin_end: float
    count: int
    mean_confidence: float | None
    accuracy: float | None


class CalibrationReportOut(BaseModel):
    sample_size: int
    brier_score: float | None
    expected_calibration_error: float | None
    bins: list[ReliabilityBinOut]
    high_confidence_error_rate: float | None
    preliminary: bool


class AblationSeamOut(BaseModel):
    """Loosely-typed on purpose: each of the six seams has a different real
    shape (routing agreement rates vs. per-case confidence deltas), and this
    schema's job is to guarantee every seam is a real, present, structured
    object -- never a missing key or a raw unvalidated blob -- not to force
    a one-size-fits-all shape onto genuinely different experiments."""

    model_config = {"extra": "allow"}


class AblationSuiteOut(BaseModel):
    harness_version: str
    ablations: dict[str, AblationSeamOut]
    methodology_note: str


class EfficiencyFrontierOut(BaseModel):
    run_id: uuid.UUID
    engine_version: str
    case_count: int
    frontier: list[dict]
    rows: list[dict]
    cost_note: str
    preliminary: bool


class ThresholdTuningOut(BaseModel):
    run_id: uuid.UUID
    case_count: int
    combinations_swept: int
    current_defaults: dict
    empirical_best: dict | None
    matches_current_defaults: bool
    current_defaults_tied_for_best: bool
    all_results: list[dict]
    preliminary: bool
    methodology_note: str


class AdversarialSuiteOut(BaseModel):
    engine_version: str
    case_count: int
    passed_count: int
    all_passed: bool
    cases: list[dict]
    methodology_note: str


class FallbackFidelityOut(BaseModel):
    model_config = {"extra": "allow"}

    engine_version: str
    measurable: bool
    methodology_note: str


class FairnessProbeOut(BaseModel):
    engine_version: str
    pair_count: int
    rows: list[dict]
    max_absolute_correctness_delta: float
    disclaimer: str


class DriftCanaryOut(BaseModel):
    engine_version: str
    baseline_frozen_at: str
    baseline_engine: str
    tolerance: float
    case_count: int
    any_drifted: bool
    cases: list[dict]
    methodology_note: str


class LiveCriticToggleRequest(BaseModel):
    transcript: str = Field(min_length=1, max_length=4000)
    question_prompt: str | None = None
    expected_keywords: list[str] | None = None


class LiveCriticToggleOut(BaseModel):
    engine_version: str
    transcript: str
    technical_confidence: float
    communication_confidence: float
    critic_off_confidence: float
    critic_on_confidence: float
    delta: float
    issues_found: list[str]
    verdict: str


class ResearchReportOut(BaseModel):
    model_config = {"extra": "allow"}

    report_version: str
    generated_at: str
    calibration: dict
    ablations: dict
    efficiency_frontier: dict
    threshold_tuning: dict
    adversarial_suite: dict
    fallback_fidelity: dict
    fairness_probe: dict
    drift_canary: dict
