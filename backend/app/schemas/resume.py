import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.graphrag.schemas import ConceptInsightOut
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
    is_active: bool
    superseded_at: datetime | None
    sections: list[ResumeSectionOut]
    resume_skills: list[ResumeSkillOut]


class ResumeSummaryOut(BaseModel):
    """Lightweight row for the resume-history list -- no sections/skills, so
    a student with many resume versions doesn't pull full parsed content for
    every row just to render the history list."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_size: int
    parsing_status: str
    uploaded_at: datetime
    parsed_at: datetime | None
    is_active: bool
    superseded_at: datetime | None
    skill_count: int


class BulletGradeOut(BaseModel):
    section_type: str
    text: str
    strength: str
    has_action_verb: bool
    has_metric: bool
    has_outcome_language: bool
    fix_suggestion: str | None


class SelfConsistencyFlagOut(BaseModel):
    skill_id: str
    skill_name: str
    message: str


class ParseabilityOut(BaseModel):
    score: float
    warnings: list[str]


class ResumeAnalysisOut(BaseModel):
    """Bundles bullet-strength grading, the self-consistency check,
    parseability score, and resume-to-graph diagnosis into a single response
    so the redesigned Resume page can render everything from one call."""

    has_resume: bool
    bullet_grades: list[BulletGradeOut] = []
    self_consistency_flags: list[SelfConsistencyFlagOut] = []
    parseability: ParseabilityOut | None = None
    graph_diagnosis: list[ConceptInsightOut] = []


class RewriteSuggestionOut(BaseModel):
    skill_name: str
    status: str
    has_sufficient_evidence: bool
    rewritten_bullet: str | None
    note: str


class RecruiterCardOut(BaseModel):
    has_resume: bool
    trust_score: float | None
    strengths: list[str] = []
    concerns: list[str] = []
    verified_skill_count: int = 0
    total_skill_count: int = 0
    parseability_score: float | None = None
    bullet_strong_ratio: float | None = None
    disclaimer: str
