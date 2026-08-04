import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.skill import SkillOut


class JobDescriptionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    raw_text: str = Field(min_length=30, max_length=20000)


class JobRequirementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    requirement_type: str
    raw_text: str
    is_required: bool
    skill: SkillOut | None


class JobDescriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    company: str | None
    raw_text: str
    source: str
    created_at: datetime
    requirements: list[JobRequirementOut]


class MatchResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    matched_skills: list[SkillOut]
    partial_skills: list[SkillOut]
    missing_skills: list[SkillOut]
    coverage: float | None
    confidence: float | None
    explanation: str
