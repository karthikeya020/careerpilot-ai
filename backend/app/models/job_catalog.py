"""Company Job Catalog: reference data (like the skill/assessment taxonomies)
describing real-shaped job openings across sectors, used to power Job Match's
dream-company search, readiness scoring, and the "I want this job" tracked
list. Not student-owned data -- seeded once via migration, read by every
student, exactly like AssessmentDomain/Skill.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.skill import Skill

SECTOR_FAANG = "faang"
SECTOR_STARTUP = "startup"
SECTOR_RESEARCH = "research"
SECTOR_GOVERNMENT = "government"
SECTOR_CONSULTING = "consulting"
SECTOR_FINANCE = "finance"

ALL_SECTORS = [SECTOR_FAANG, SECTOR_STARTUP, SECTOR_RESEARCH, SECTOR_GOVERNMENT, SECTOR_CONSULTING, SECTOR_FINANCE]

SECTOR_LABELS = {
    SECTOR_FAANG: "FAANG / Big Tech",
    SECTOR_STARTUP: "Startup",
    SECTOR_RESEARCH: "Research",
    SECTOR_GOVERNMENT: "Government",
    SECTOR_CONSULTING: "Consulting",
    SECTOR_FINANCE: "Finance",
}


class CompanyJobListing(UUIDPKMixin, Base):
    __tablename__ = "company_job_listings"

    company: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    sector: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    seniority: Mapped[str] = mapped_column(String(50), default="entry_level", nullable=False)
    package_min_lpa: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    package_max_lpa: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    # Assessment-domain slugs this role leans on most (e.g. ["dsa", "java"]) --
    # drives "recommended practice topics" and interview-question emphasis for
    # students tracking this listing. Never a hidden scoring input by itself.
    emphasis_domains: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    requirements: Mapped[list["JobListingRequirement"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan"
    )


class JobListingRequirement(UUIDPKMixin, Base):
    __tablename__ = "job_listing_requirements"

    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("company_job_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    is_required: Mapped[bool] = mapped_column(default=True, nullable=False)

    listing: Mapped["CompanyJobListing"] = relationship(back_populates="requirements")
    skill: Mapped["Skill"] = relationship()


class TrackedJob(UUIDPKMixin, Base):
    """A student's "I want this job" list -- capped at 5 (enforced in
    app/services/job_catalog_service.py, not at the DB layer, so the error
    message can be student-friendly)."""

    __tablename__ = "tracked_jobs"
    __table_args__ = (UniqueConstraint("student_profile_id", "listing_id", name="uq_tracked_job_student_listing"),)

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("company_job_listings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    listing: Mapped["CompanyJobListing"] = relationship()
