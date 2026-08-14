import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.skill import SkillOut


class SectorOut(BaseModel):
    slug: str
    label: str
    listing_count: int


class CompanyJobListingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company: str
    title: str
    sector: str
    seniority: str
    package_min_lpa: float
    package_max_lpa: float
    description: str
    emphasis_domains: list[str]
    created_at: datetime


class JobListingMatchOut(BaseModel):
    listing: CompanyJobListingOut
    matched_skills: list[SkillOut]
    partial_skills: list[SkillOut]
    missing_skills: list[SkillOut]
    readiness: float | None
    is_tracked: bool = False


class TrackedJobOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    match: JobListingMatchOut


class GapPlanItemOut(BaseModel):
    skill_name: str
    status: str
    estimated_hours: float
    recommended_resource: dict | None


class JobGapPlanOut(BaseModel):
    listing: CompanyJobListingOut
    readiness: float | None
    matched_count: int
    partial_count: int
    missing_count: int
    total_estimated_hours: float
    weekly_commitment_hours: float
    estimated_weeks_to_ready: int
    items: list[GapPlanItemOut]
    assumptions: list[str]
