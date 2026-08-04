import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow


class DecisionTrace(UUIDPKMixin, Base):
    __tablename__ = "decision_traces"

    student_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    task_type: Mapped[str] = mapped_column(String(50), nullable=False)
    route: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    agreement: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    evidence_ids: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    agents_invoked: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    model_versions: Mapped[dict] = mapped_column(JSONBType(), default=dict, nullable=False)
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False)
    requires_human_review: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)


class AuditEvent(UUIDPKMixin, Base):
    __tablename__ = "audit_events"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    student_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONBType(), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
