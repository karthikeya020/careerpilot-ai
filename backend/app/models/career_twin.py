import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

COMPONENT_RESUME = "resume_readiness"
COMPONENT_TECHNICAL = "technical_readiness"
COMPONENT_COMMUNICATION = "communication_readiness"
COMPONENT_ASSESSMENT = "assessment_readiness"
COMPONENT_PORTFOLIO = "portfolio_readiness"
COMPONENT_ROLE_ALIGNMENT = "role_alignment_readiness"

ALL_COMPONENTS = [
    COMPONENT_RESUME,
    COMPONENT_TECHNICAL,
    COMPONENT_COMMUNICATION,
    COMPONENT_ASSESSMENT,
    COMPONENT_PORTFOLIO,
    COMPONENT_ROLE_ALIGNMENT,
]

STATUS_SCORED = "scored"
STATUS_INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class CareerTwinSnapshot(UUIDPKMixin, Base):
    __tablename__ = "career_twin_snapshots"
    __table_args__ = (UniqueConstraint("student_profile_id", "version", name="uq_twin_version"),)

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    formula_version: Mapped[str] = mapped_column(String(30), nullable=False)
    change_summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    score_delta: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    previous_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("career_twin_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    components: Mapped[list["ReadinessComponent"]] = relationship(
        back_populates="snapshot", cascade="all, delete-orphan"
    )


class ReadinessComponent(UUIDPKMixin, Base):
    __tablename__ = "readiness_components"

    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("career_twin_snapshots.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component_type: Mapped[str] = mapped_column(String(40), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default=STATUS_SCORED, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    # twin-v2 small-sample safeguard (see docs/implementation/CAREER_TWIN_SCORING.md
    # "Small-sample safeguard"): evidence_diversity is the count of distinct
    # source_object_type values behind this component's evidence;
    # is_low_sample is true when evidence_count or evidence_diversity falls
    # below the stability thresholds, in which case `score`/`confidence` were
    # already shrunk/capped and `explanation` carries the low-sample notice.
    evidence_diversity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_low_sample: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # twin-v2 freshness safeguard (see docs/implementation/CAREER_TWIN_SCORING.md
    # "Evidence freshness"): stale_evidence_fraction is the share of this
    # component's evidence older than the staleness threshold at scoring
    # time; is_stale_evidence is true when a majority of the evidence is
    # stale, in which case confidence was already capped and `explanation`
    # carries the freshness notice.
    stale_evidence_fraction: Mapped[float] = mapped_column(Numeric(5, 4), default=0.0, nullable=False)
    is_stale_evidence: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    snapshot: Mapped["CareerTwinSnapshot"] = relationship(back_populates="components")
