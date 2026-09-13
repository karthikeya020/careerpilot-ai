import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow


class LeetCodeCompletion(UUIDPKMixin, Base):
    """A LeetCode problem the student marked complete from the practice plan.
    Optional `code` + `analysis` hold the "explain how you solved" review.
    This is the only progress the Assessment page tracks now -- quiz
    responses feed weakness detection only."""

    __tablename__ = "leetcode_completions"
    __table_args__ = (
        UniqueConstraint("student_profile_id", "problem_slug", name="uq_leetcode_completion_student_slug"),
    )

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    problem_slug: Mapped[str] = mapped_column(String(160), nullable=False)
    problem_title: Mapped[str] = mapped_column(String(200), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(10), default="", nullable=False)
    # Which weak concept / domain this problem was recommended against, if any.
    concept_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    domain_slug: Mapped[str | None] = mapped_column(String(50), nullable=True)

    code: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Serialized CodeReviewOut from the code-review agent.
    analysis: Mapped[dict | None] = mapped_column(JSONBType(), nullable=True)
    analyzed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    completed_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
