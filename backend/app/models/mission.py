import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.assessment import Concept
    from app.models.skill import Skill

MISSION_STATUS_PENDING = "pending"
MISSION_STATUS_IN_PROGRESS = "in_progress"
MISSION_STATUS_COMPLETED = "completed"
MISSION_STATUS_DISMISSED = "dismissed"


class LearningMission(UUIDPKMixin, Base):
    __tablename__ = "learning_missions"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_skill_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("skills.id"), nullable=True)
    target_concept_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("concepts.id"), nullable=True)
    source_component: Mapped[str] = mapped_column(String(40), nullable=False)
    priority_rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=MISSION_STATUS_PENDING, nullable=False)
    evidence_ids: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    # Phase 2 autonomous-loop fields. `tasks` is a list[str] of concrete
    # steps; `root_cause` stores the GraphRAG root-cause path (or
    # relational-fallback path) that produced this mission, so the Trust
    # Center can show exactly why it was generated. `expected_impact_*` is
    # always presented as an estimate, never a guarantee (Prompt 2 rule).
    tasks: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    estimated_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    root_cause: Mapped[dict | None] = mapped_column(JSONBType(), nullable=True)
    resource_ids: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    expected_impact_estimate: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    expected_impact_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    # Populated once the student completes a follow-up assessment tied to
    # this mission (see autonomous_loop_service.reassess_and_close_mission).
    outcome_evidence_ids: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    actual_observed_change: Mapped[dict | None] = mapped_column(JSONBType(), nullable=True)

    target_skill: Mapped["Skill | None"] = relationship()
    target_concept: Mapped["Concept | None"] = relationship()
