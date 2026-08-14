import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssessmentDomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    description: str
    question_count: int = 0
    recommended: bool = False
    matched_skills: list[str] = []


class QuestionOut(BaseModel):
    """Never includes `correct_answer` -- that would leak the rubric to the
    student taking the assessment."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_type: str
    prompt: str
    options: list | None
    difficulty: int
    difficulty_band: str
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
    explanation: str = ""


class AttemptProgressOut(BaseModel):
    attempt_id: uuid.UUID
    response: QuestionResponseOut | None = None
    next_question: QuestionOut | None
    is_complete: bool
    domain_exhausted: bool = False
    answered_in_domain: int = 0
    total_in_domain: int = 0


class AssessmentAttemptOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    domain: AssessmentDomainOut
    status: str
    score: float | None
    confidence: float | None
    started_at: datetime
    completed_at: datetime | None


class ActivityDayOut(BaseModel):
    date: str
    count: int
    correct_count: int


class ActivityDayDetailOut(BaseModel):
    response_id: uuid.UUID
    question_id: uuid.UUID
    prompt: str
    domain_name: str
    concept_name: str
    difficulty: int
    difficulty_band: str
    question_type: str
    is_correct: bool | None
    score: float | None
    submitted_at: datetime


class DomainAccuracyOut(BaseModel):
    domain: str
    accuracy: float
    answered: int


class DifficultyAccuracyOut(BaseModel):
    band: str
    accuracy: float
    answered: int


class ScoreTrendPointOut(BaseModel):
    date: str
    avg_score: float


class AssessmentAnalyticsOut(BaseModel):
    total_answered: int
    total_correct: int
    overall_accuracy: float | None
    accuracy_by_domain: list[DomainAccuracyOut]
    accuracy_by_difficulty: list[DifficultyAccuracyOut]
    score_trend: list[ScoreTrendPointOut]
    current_streak_days: int
    longest_streak_days: int
    active_day_count: int
