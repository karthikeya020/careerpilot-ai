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
