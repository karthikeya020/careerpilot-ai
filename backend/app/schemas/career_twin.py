import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReadinessComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    component_type: str
    score: float | None
    confidence: float | None
    status: str
    evidence_count: int
    explanation: str
    # Derived, not stored: trend is this component's score delta versus the
    # same component in the previous snapshot (None if there is no previous
    # snapshot or the component wasn't scored then); uncertainty is simply
    # 1 - confidence, surfaced explicitly so the UI never has to compute it
    # itself. Neither is a new source of evidence -- both are recomputed
    # on every read from already-stored snapshot data.
    trend: float | None = None
    uncertainty: float | None = None
    # twin-v2 small-sample safeguard fields -- see
    # docs/implementation/CAREER_TWIN_SCORING.md "Small-sample safeguard".
    # evidence_diversity is the count of distinct source_object_type values
    # behind this component; is_low_sample/low_sample_notice surface when
    # score/confidence were shrunk/capped because the evidence is too
    # sparse or too narrowly sourced to support a confident estimate.
    evidence_diversity: int = 0
    is_low_sample: bool = False
    low_sample_notice: str | None = None


class CareerTwinSnapshotOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version: int
    overall_score: float | None
    overall_confidence: float | None
    evidence_count: int
    formula_version: str
    change_summary: str
    score_delta: float | None
    created_at: datetime
    components: list[ReadinessComponentOut]
