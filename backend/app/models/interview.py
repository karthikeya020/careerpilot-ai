"""Interview Arena data model.

Mirrors the assessment engine's shape (session -> question -> response) but
for voice/typed mock interviews: `InterviewSession` -> `InterviewQuestion` ->
`InterviewAnswer` -> `InterviewEvaluation`. An answer always has a transcript
(from live speech-to-text, a deterministic demo fixture, or typed text -- see
`transcript_source`); evaluation always traces back to a `CareExecution` so
the Trust Center can show exactly which agents were invoked and why
(Constitution rule 3).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.assessment import Concept
    from app.models.care import CareExecution
    from app.models.job_description import JobDescription
    from app.models.student import TargetRole

INTERVIEW_MODE_HR = "hr"
INTERVIEW_MODE_TECHNICAL = "technical"
INTERVIEW_MODE_RESUME = "resume"
INTERVIEW_MODE_ROLE_SPECIFIC = "role_specific"
INTERVIEW_MODE_COMPANY_CONTEXT = "company_context"
INTERVIEW_MODE_MIXED = "mixed"
ALL_INTERVIEW_MODES = [
    INTERVIEW_MODE_HR,
    INTERVIEW_MODE_TECHNICAL,
    INTERVIEW_MODE_RESUME,
    INTERVIEW_MODE_ROLE_SPECIFIC,
    INTERVIEW_MODE_COMPANY_CONTEXT,
    INTERVIEW_MODE_MIXED,
]

INTERVIEW_STATUS_IN_PROGRESS = "in_progress"
INTERVIEW_STATUS_COMPLETED = "completed"

TRANSCRIPT_SOURCE_TYPED = "typed"
TRANSCRIPT_SOURCE_LIVE_STT = "live_stt"
TRANSCRIPT_SOURCE_DETERMINISTIC_DEMO = "deterministic_demo"
TRANSCRIPT_SOURCE_UNAVAILABLE = "unavailable"

# Resume-claim evidence-check classifications (see app/agents/resume_evidence_agent.py).
EVIDENCE_CHECK_SUPPORTED = "supported_by_resume_evidence"
EVIDENCE_CHECK_PARTIAL = "partially_supported"
EVIDENCE_CHECK_NOT_SUPPORTED = "not_currently_supported"
EVIDENCE_CHECK_CONTRADICTED = "contradicted_by_uploaded_evidence"
EVIDENCE_CHECK_INSUFFICIENT = "insufficient_evidence"


class InterviewSession(UUIDPKMixin, Base):
    __tablename__ = "interview_sessions"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mode: Mapped[str] = mapped_column(String(30), nullable=False)
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("target_roles.id"), nullable=True)
    job_description_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("job_descriptions.id"), nullable=True
    )
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=INTERVIEW_STATUS_IN_PROGRESS, nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    overall_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    started_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    target_role: Mapped["TargetRole | None"] = relationship()
    job_description: Mapped["JobDescription | None"] = relationship()
    questions: Mapped[list["InterviewQuestion"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="InterviewQuestion.order_index"
    )


class InterviewQuestion(UUIDPKMixin, Base):
    __tablename__ = "interview_questions"

    session_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # "bank" (curated question bank), "job_description" (drawn from JD
    # requirements), or "resume" (drawn from a resume claim to probe).
    question_source: Mapped[str] = mapped_column(String(30), nullable=False)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("concepts.id"), nullable=True)
    expected_keywords: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    session: Mapped["InterviewSession"] = relationship(back_populates="questions")
    concept: Mapped["Concept | None"] = relationship()
    answer: Mapped["InterviewAnswer | None"] = relationship(
        back_populates="question", cascade="all, delete-orphan", uselist=False
    )


class InterviewAnswer(UUIDPKMixin, Base):
    __tablename__ = "interview_answers"

    question_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    audio_storage_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    audio_mime_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    audio_duration_seconds: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=False)
    transcript_source: Mapped[str] = mapped_column(String(30), nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    question: Mapped["InterviewQuestion"] = relationship(back_populates="answer")
    evaluation: Mapped["InterviewEvaluation | None"] = relationship(
        back_populates="answer", cascade="all, delete-orphan", uselist=False
    )


class InterviewEvaluation(UUIDPKMixin, Base):
    __tablename__ = "interview_evaluations"

    answer_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("interview_answers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    care_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("care_executions.id"), nullable=True
    )
    # dict[str, float] keyed by rubric dimension name (only dimensions
    # actually applicable to this question's mode are present -- Constitution
    # rule 1, never invent a score for a dimension with no evidence).
    dimension_scores: Mapped[dict] = mapped_column(JSONBType(), nullable=False)
    overall_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    agreement: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    strengths: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    improvements: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    # list[{"claim": str, "classification": str, "explanation": str}]
    evidence_checks: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    communication_metrics: Mapped[dict] = mapped_column(JSONBType(), default=dict, nullable=False)
    # list[{"type": str, "label": str, "position_percent": float}]
    timeline_markers: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    better_answer_framework: Mapped[str] = mapped_column(Text, default="", nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    answer: Mapped["InterviewAnswer"] = relationship(back_populates="evaluation")
    care_execution: Mapped["CareExecution | None"] = relationship()
