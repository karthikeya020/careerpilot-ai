import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StartInterviewRequest(BaseModel):
    mode: str
    target_role_id: uuid.UUID | None = None
    job_description_id: uuid.UUID | None = None
    company_name: str | None = None


class InterviewQuestionOut(BaseModel):
    """Never includes `expected_keywords` -- that's the grading rubric, kept
    server-side the same way assessment questions never expose
    `correct_answer` to the student taking them."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_index: int
    mode: str
    prompt: str
    question_source: str


class InterviewAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    transcript: str
    transcript_source: str
    audio_duration_seconds: float | None
    has_audio: bool = False
    submitted_at: datetime


class InterviewEvaluationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    care_execution_id: uuid.UUID | None
    dimension_scores: dict
    overall_score: float
    confidence: float
    agreement: float | None
    strengths: list[str]
    improvements: list[str]
    evidence_checks: list[dict]
    communication_metrics: dict
    timeline_markers: list[dict]
    better_answer_framework: str
    requires_human_review: bool
    created_at: datetime


class InterviewSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mode: str
    target_role_id: uuid.UUID | None
    job_description_id: uuid.UUID | None
    company_name: str | None
    status: str
    overall_score: float | None
    overall_confidence: float | None
    started_at: datetime
    completed_at: datetime | None


class InterviewProgressOut(BaseModel):
    session: InterviewSessionOut
    answer: InterviewAnswerOut | None = None
    evaluation: InterviewEvaluationOut | None = None
    next_question: InterviewQuestionOut | None
    is_complete: bool


class InterviewReplayItemOut(BaseModel):
    question: InterviewQuestionOut
    answer: InterviewAnswerOut
    evaluation: InterviewEvaluationOut | None


class InterviewReplayOut(BaseModel):
    session: InterviewSessionOut
    items: list[InterviewReplayItemOut]
