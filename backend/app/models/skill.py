import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import TimestampMixin, UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.assessment import Concept

# Evidence types feeding SkillEvidence.
EVIDENCE_TYPE_RESUME = "resume"
EVIDENCE_TYPE_SELF_ASSESSMENT = "self_assessment"
EVIDENCE_TYPE_JOB_MATCH = "job_description_match"
EVIDENCE_TYPE_ONBOARDING = "onboarding"
EVIDENCE_TYPE_PROJECT = "project"
EVIDENCE_TYPE_ASSESSMENT = "technical_assessment"


class Skill(UUIDPKMixin, Base):
    __tablename__ = "skills"

    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    aliases: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)


class StudentSkill(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "student_skills"
    __table_args__ = (UniqueConstraint("student_profile_id", "skill_id", name="uq_student_skill"),)

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    self_rating: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    skill: Mapped["Skill"] = relationship()


class SkillEvidence(UUIDPKMixin, Base):
    __tablename__ = "skill_evidence"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("concepts.id"), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_object_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_object_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    raw_score: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    normalized_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    weight: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=1.0)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    skill: Mapped["Skill"] = relationship()
    concept: Mapped["Concept | None"] = relationship()
