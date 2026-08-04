import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import TimestampMixin, UUIDPKMixin

if TYPE_CHECKING:
    from app.models.user import User


class StudentProfile(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "student_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_settings: Mapped[dict] = mapped_column(JSONBType(), default=dict, nullable=False)
    primary_target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(),
        ForeignKey(
            "target_roles.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_student_profiles_primary_target_role_id",
        ),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="student_profile")
    career_goals: Mapped[list["CareerGoal"]] = relationship(
        back_populates="student_profile",
        cascade="all, delete-orphan",
        foreign_keys="CareerGoal.student_profile_id",
    )
    target_roles: Mapped[list["TargetRole"]] = relationship(
        back_populates="student_profile",
        cascade="all, delete-orphan",
        foreign_keys="TargetRole.student_profile_id",
    )
    primary_target_role: Mapped["TargetRole | None"] = relationship(
        foreign_keys=[primary_target_role_id], post_update=True
    )


class CareerGoal(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "career_goals"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    description: Mapped[str] = mapped_column(Text, nullable=False)
    timeline_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship(
        back_populates="career_goals", foreign_keys=[student_profile_id]
    )


class TargetRole(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "target_roles"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    seniority: Mapped[str] = mapped_column(String(50), default="entry_level", nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    student_profile: Mapped["StudentProfile"] = relationship(
        back_populates="target_roles", foreign_keys=[student_profile_id]
    )
