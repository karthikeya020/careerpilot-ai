import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.skill import Skill
    from app.models.student import TargetRole

QUESTION_TYPE_MULTIPLE_CHOICE = "multiple_choice"
QUESTION_TYPE_MULTIPLE_SELECTION = "multiple_selection"
QUESTION_TYPE_SHORT_ANSWER = "short_answer"
QUESTION_TYPE_CODE_READING = "code_reading"
QUESTION_TYPE_CONCEPT_EXPLANATION = "concept_explanation"

DETERMINISTIC_QUESTION_TYPES = {QUESTION_TYPE_MULTIPLE_CHOICE, QUESTION_TYPE_MULTIPLE_SELECTION}
AI_GRADED_QUESTION_TYPES = {
    QUESTION_TYPE_SHORT_ANSWER,
    QUESTION_TYPE_CODE_READING,
    QUESTION_TYPE_CONCEPT_EXPLANATION,
}

ATTEMPT_STATUS_IN_PROGRESS = "in_progress"
ATTEMPT_STATUS_COMPLETED = "completed"


class AssessmentDomain(UUIDPKMixin, Base):
    __tablename__ = "assessment_domains"

    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)


class Concept(UUIDPKMixin, Base):
    __tablename__ = "concepts"
    __table_args__ = (UniqueConstraint("domain_id", "slug", name="uq_concept_domain_slug"),)

    domain_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assessment_domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    skill_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("skills.id"), nullable=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    skill: Mapped["Skill | None"] = relationship()
    domain: Mapped["AssessmentDomain"] = relationship()


class ConceptDependency(Base):
    """`concept_id` DEPENDS_ON `depends_on_id` -- mirrored 1:1 into Neo4j at
    seed time (see app/graphrag/seed.py). This table is the source of truth;
    Neo4j is the traversal/visualization layer (see PHASE_2_EXECUTION_PLAN
    §2.3)."""

    __tablename__ = "concept_dependencies"

    concept_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )
    depends_on_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True
    )


class Question(UUIDPKMixin, Base):
    __tablename__ = "questions"

    domain_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assessment_domains.id", ondelete="CASCADE"), nullable=False, index=True
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("concepts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_type: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # MCQ/multi-select: list[{"id": str, "text": str}]. Free-form types: null.
    options: Mapped[list | None] = mapped_column(JSONBType(), nullable=True)
    # MCQ/multi-select: {"correct_option_ids": [...]}.
    # Free-form: {"keywords": [...], "sample_answer": "..."} used by the AI
    # evaluator (or its deterministic keyword-overlap fallback).
    correct_answer: Mapped[dict] = mapped_column(JSONBType(), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=2)  # 1 (easiest) - 5 (hardest)
    target_role_relevance: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    concept: Mapped["Concept"] = relationship()


class AssessmentAttempt(UUIDPKMixin, Base):
    __tablename__ = "assessment_attempts"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    domain_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("assessment_domains.id"), nullable=False)
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("target_roles.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ATTEMPT_STATUS_IN_PROGRESS, nullable=False)
    started_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)

    domain: Mapped["AssessmentDomain"] = relationship()
    target_role: Mapped["TargetRole | None"] = relationship()
    responses: Mapped[list["QuestionResponse"]] = relationship(
        back_populates="attempt", cascade="all, delete-orphan", order_by="QuestionResponse.created_at"
    )


class QuestionResponse(UUIDPKMixin, Base):
    __tablename__ = "question_responses"

    attempt_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("assessment_attempts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    question_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("questions.id"), nullable=False)
    concept_id: Mapped[uuid.UUID] = mapped_column(GUID(), ForeignKey("concepts.id"), nullable=False)
    response_payload: Mapped[dict] = mapped_column(JSONBType(), nullable=False)
    is_correct: Mapped[bool | None] = mapped_column(nullable=True)
    score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    ai_evaluated: Mapped[bool] = mapped_column(default=False, nullable=False)
    evaluator_confidence: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    time_spent_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    attempt: Mapped["AssessmentAttempt"] = relationship(back_populates="responses")
    question: Mapped["Question"] = relationship()
    concept: Mapped["Concept"] = relationship()
