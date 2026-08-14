import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class StartInterviewRequest(BaseModel):
    mode: str
    target_role_id: uuid.UUID | None = None
    job_description_id: uuid.UUID | None = None
    company_name: str | None = None


class InterviewQuestionOut(BaseModel):
    """Never includes `expected_keywords` or `model_answer_summary` -- those
    are the grading rubric and reference answer, kept server-side the same
    way assessment questions never expose `correct_answer` to the student
    taking them. `difficulty` is safe to expose live -- it doesn't leak the
    rubric, and signaling round structure up front is normal for a real
    interview."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_index: int
    mode: str
    prompt: str
    difficulty: str
    question_source: str
    is_follow_up: bool
    follow_up_rationale: str | None


class InterviewReplayQuestionOut(InterviewQuestionOut):
    """Replay/report-only view -- the round is already over, so revealing
    the reference answer here is safe and is the whole point of the report."""

    model_answer_summary: str


class InterviewAnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    transcript: str
    transcript_source: str
    audio_duration_seconds: float | None
    audio_mime_type: str | None = None
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
    question: InterviewReplayQuestionOut
    answer: InterviewAnswerOut
    evaluation: InterviewEvaluationOut | None


class DifficultyBreakdownOut(BaseModel):
    difficulty: str
    average_score: float | None
    question_count: int


class InterviewRoundSummaryOut(BaseModel):
    """Every number here traces directly to stored InterviewEvaluation rows
    (see interview_service.build_round_summary) -- no new LLM call, so
    nothing here can be an invented figure (Constitution rule 1)."""

    overall_score: float | None
    overall_confidence: float | None
    scripted_question_count: int
    follow_up_count: int
    difficulty_breakdown: list[DifficultyBreakdownOut]
    dimension_averages: dict[str, float]
    communication_rollup: dict
    narrative_summary: str


class InterviewReplayOut(BaseModel):
    session: InterviewSessionOut
    items: list[InterviewReplayItemOut]
    summary: InterviewRoundSummaryOut
