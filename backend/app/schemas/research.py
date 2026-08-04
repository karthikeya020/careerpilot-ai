import uuid
from datetime import datetime

from pydantic import BaseModel


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
