import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.skill import Skill

JD_SOURCE_PASTED = "pasted"
JD_SOURCE_UPLOADED = "uploaded"

REQUIREMENT_SKILL = "skill"
REQUIREMENT_EXPERIENCE = "experience"
REQUIREMENT_EDUCATION = "education"
REQUIREMENT_RESPONSIBILITY = "responsibility"


class JobDescription(UUIDPKMixin, Base):
    __tablename__ = "job_descriptions"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default=JD_SOURCE_PASTED, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    requirements: Mapped[list["JobRequirement"]] = relationship(
        back_populates="job_description", cascade="all, delete-orphan"
    )


class JobRequirement(UUIDPKMixin, Base):
    __tablename__ = "job_requirements"

    job_description_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False
    )
    requirement_type: Mapped[str] = mapped_column(String(30), nullable=False)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("skills.id"), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    job_description: Mapped["JobDescription"] = relationship(back_populates="requirements")
    skill: Mapped["Skill | None"] = relationship()
