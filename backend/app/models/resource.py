import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.assessment import Concept
    from app.models.skill import Skill

RESOURCE_TYPE_ARTICLE = "article"
RESOURCE_TYPE_VIDEO = "video"
RESOURCE_TYPE_INTERACTIVE = "interactive"
RESOURCE_TYPE_DOCUMENTATION = "documentation"
RESOURCE_TYPE_COURSE = "course"


class Resource(UUIDPKMixin, Base):
    __tablename__ = "resources"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(150), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(30), nullable=False)
    skill_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("skills.id"), nullable=True)
    concept_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), ForeignKey("concepts.id"), nullable=True)
    difficulty: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    quality_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0.8)
    language: Mapped[str] = mapped_column(String(20), nullable=False, default="en")
    cost: Mapped[str] = mapped_column(String(20), nullable=False, default="free")
    prerequisites: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    source_verified: Mapped[bool] = mapped_column(default=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    skill: Mapped["Skill | None"] = relationship()
    concept: Mapped["Concept | None"] = relationship()
