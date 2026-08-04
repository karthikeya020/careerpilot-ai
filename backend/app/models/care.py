import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

CARE_ROUTE_DETERMINISTIC = "deterministic"
CARE_ROUTE_SINGLE_AGENT = "single_agent"
CARE_ROUTE_GRAPHRAG_AGENT = "graphrag_agent"
CARE_ROUTE_MULTI_AGENT = "multi_agent"
CARE_ROUTE_CRITIC_REFLECTION = "critic_reflection"
CARE_ROUTE_HUMAN_REVIEW = "human_review"

CARE_STATUS_COMPLETED = "completed"
CARE_STATUS_FAILED = "failed"


class CareExecution(UUIDPKMixin, Base):
    """One row per CARE routing decision. This is the Trust Center's
    primary data source -- every field the spec requires ("request, task
    type, input evidence, selected route, routing factors, agents invoked,
    retrieval used, reflection used, confidence, cost, latency, final
    status, human-review status, policy version") is a real column, not
    reconstructed after the fact."""

    __tablename__ = "care_executions"

    student_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    request_summary: Mapped[str] = mapped_column(Text, nullable=False)
    input_evidence_ids: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    routing_factors: Mapped[dict] = mapped_column(JSONBType(), nullable=False)
    route: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    agents_invoked: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    retrieval_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    reflection_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    agreement: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), nullable=False, default=0.0)
    latency_ms: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False, default=0.0)
    final_status: Mapped[str] = mapped_column(String(20), default=CARE_STATUS_COMPLETED, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False, index=True)

    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="care_execution", cascade="all, delete-orphan")


class AgentRun(UUIDPKMixin, Base):
    """One row per specialist-agent invocation inside a CareExecution."""

    __tablename__ = "agent_runs"

    care_execution_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("care_executions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[str] = mapped_column(String(60), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(30), nullable=False)
    input_payload: Mapped[dict] = mapped_column(JSONBType(), nullable=False)
    output_payload: Mapped[dict] = mapped_column(JSONBType(), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    evidence_citations: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    inference_type: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default=CARE_STATUS_COMPLETED, nullable=False)
    latency_ms: Mapped[float] = mapped_column(Numeric(10, 3), nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    care_execution: Mapped["CareExecution"] = relationship(back_populates="agent_runs")
