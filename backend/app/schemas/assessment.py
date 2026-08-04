import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssessmentDomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str


class QuestionOut(BaseModel):
    """Never includes `correct_answer` -- that would leak the rubric to the
    student taking the assessment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_type: str
    prompt: str
    options: list | None
    difficulty: int
    concept_name: str


class StartAttemptRequest(BaseModel):
    domain_slug: str
    target_role_id: uuid.UUID | None = None


class SubmitResponseRequest(BaseModel):
    question_id: uuid.UUID
    response_payload: dict
    time_spent_seconds: int | None = None


class QuestionResponseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    is_correct: bool | None
    score: float | None
    ai_evaluated: bool


class AttemptProgressOut(BaseModel):
    attempt_id: uuid.UUID
    response: QuestionResponseOut | None = None
    next_question: QuestionOut | None
    is_complete: bool


class AssessmentAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: AssessmentDomainOut
    status: str
    score: float | None
    confidence: float | None
    started_at: datetime
    completed_at: datetime | None
