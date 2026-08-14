import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RippleNoteOut(BaseModel):
    target_component: str
    reason: str


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
    # twin-v2 freshness safeguard -- see docs/implementation/CAREER_TWIN_SCORING.md
    # "Evidence freshness". stale_evidence_fraction is the share (by count)
    # of this component's evidence older than 6 months at scoring time;
    # is_stale_evidence/stale_evidence_notice surface when a majority is
    # stale and confidence was capped as a result.
    stale_evidence_fraction: float = 0.0
    is_stale_evidence: bool = False
    stale_evidence_notice: str | None = None
    # Ripple-effect: other components whose evidence overlaps this one's,
    # directly (shared skill) or one graph hop away (shared concept
    # dependency) -- see app/career_twin/ripple.py. Derived at read time.
    ripple_notes: list["RippleNoteOut"] = []
    # Evidence provenance: this component's evidence weight broken down by
    # evidence_type (e.g. {"technical_assessment": 0.4, "interview": 0.35,
    # "resume": 0.25}) -- see app/career_twin/scoring.py. Derived at read time.
    provenance: dict[str, float] = {}


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
    # Milestone moments: quiet, purely self-comparative callouts -- a
    # component crossing 70% for the first time, or an insufficient_evidence
    # flag finally resolving. Derived by diffing against the previous
    # snapshot at read time; never stored, never a cross-student comparison
    # (Constitution rule 6).
    milestones: list[str] = []


class RoleAlignmentOut(BaseModel):
    role_title: str
    alignment: float
    matched_skills: list[str]
    missing_skills: list[str]


class ComponentProjectionOut(BaseModel):
    component_type: str
    current_score: float | None
    status: str
    weeks_to_target: int | None = None
    weeks_to_target_low: int | None = None
    weeks_to_target_high: int | None = None
    weekly_rate: float | None = None
    note: str


class EvidenceCitationOut(BaseModel):
    skill_name: str
    evidence_type: str
    explanation: str
    created_at: str


class ComponentProofOut(BaseModel):
    component_type: str
    score: float | None
    confidence: float | None
    status: str
    evidence_count: int
    citations: list[EvidenceCitationOut]


class SnapshotProofOut(BaseModel):
    student_name: str
    target_role: str | None
    version: int
    created_at: str
    overall_score: float | None
    overall_confidence: float | None
    formula_version: str
    components: list[ComponentProofOut]
    disclaimer: str
