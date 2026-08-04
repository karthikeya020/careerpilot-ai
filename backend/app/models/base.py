import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.core.types import GUID


def utcnow() -> datetime:
    """Naive UTC timestamp. SQLite does not round-trip tz-aware datetimes the
    way Postgres does, so all timestamps in this codebase are stored and
    compared as naive UTC by convention."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class UUIDPKMixin:
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(), default=utcnow, onupdate=utcnow, nullable=False)
