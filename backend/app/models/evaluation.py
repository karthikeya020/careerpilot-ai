import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow


class EvaluationRun(UUIDPKMixin, Base):
    """One invocation of `python -m app.evaluation.run` -- groups results
    from comparing route variants over the curated case set (docs
    06_EVALUATION_PLAN Experiment A)."""

    __tablename__ = "evaluation_runs"

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    dataset_name: Mapped[str] = mapped_column(String(100), nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    results: Mapped[list["EvaluationResult"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class EvaluationResult(UUIDPKMixin, Base):
    __tablename__ = "evaluation_results"

    run_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    case_id: Mapped[str] = mapped_column(String(100), nullable=False)
    route_variant: Mapped[str] = mapped_column(String(30), nullable=False)
    route_selected: Mapped[str] = mapped_column(String(30), nullable=False)
    agents_invoked: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    agreement: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    latency_ms: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False)
    token_usage: Mapped[dict] = mapped_column(JSONBType(), default=dict, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0.0)
    accuracy_label: Mapped[str | None] = mapped_column(String(20), nullable=True)
    failure: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    run: Mapped["EvaluationRun"] = relationship(back_populates="results")
