import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.skill import SkillOut


class ResumeSectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_type: str
    heading: str
    raw_text: str
    order_index: int


class ResumeSkillOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    skill: SkillOut
    confidence: float
    evidence_snippet: str


class ResumeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    content_type: str
    file_size: int
    parsing_status: str
    parsing_error: str | None
    uploaded_at: datetime
    parsed_at: datetime | None
    sections: list[ResumeSectionOut]
    resume_skills: list[ResumeSkillOut]
