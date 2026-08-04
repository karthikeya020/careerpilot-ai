import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.skill import Skill

PARSING_STATUS_PENDING = "pending"
PARSING_STATUS_PARSED = "parsed"
PARSING_STATUS_FAILED = "failed"

SECTION_SUMMARY = "summary"
SECTION_EDUCATION = "education"
SECTION_EXPERIENCE = "experience"
SECTION_PROJECTS = "projects"
SECTION_SKILLS = "skills"
SECTION_CERTIFICATIONS = "certifications"
SECTION_ACHIEVEMENTS = "achievements"
SECTION_OTHER = "other"


class Resume(UUIDPKMixin, Base):
    __tablename__ = "resumes"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    parsing_status: Mapped[str] = mapped_column(String(20), default=PARSING_STATUS_PENDING, nullable=False)
    parsing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    parsed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    sections: Mapped[list["ResumeSection"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan", order_by="ResumeSection.order_index"
    )
    resume_skills: Mapped[list["ResumeSkill"]] = relationship(back_populates="resume", cascade="all, delete-orphan")


class ResumeSection(UUIDPKMixin, Base):
    __tablename__ = "resume_sections"

    resume_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    section_type: Mapped[str] = mapped_column(String(30), nullable=False)
    heading: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    resume: Mapped["Resume"] = relationship(back_populates="sections")


class ResumeSkill(UUIDPKMixin, Base):
    __tablename__ = "resume_skills"
    __table_args__ = (UniqueConstraint("resume_id", "skill_id", name="uq_resume_skill"),)

    resume_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    evidence_snippet: Mapped[str] = mapped_column(Text, default="", nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False, default=0.6)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    resume: Mapped["Resume"] = relationship(back_populates="resume_skills")
    skill: Mapped["Skill"] = relationship()
