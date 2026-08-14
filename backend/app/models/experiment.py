"""Career Experiment Lab data model. A scenario is a set of hour
allocations (`SCENARIO SCHEMA`: skill + activity type + hours) the student
is considering; a result is the deterministic simulation engine's output for
that scenario, always paired with the engine version that produced it
(Constitution rule 10 -- validated, versioned, never a raw unvalidated dict
in the trust path) and never containing an LLM-computed number (Prompt 3:
"the LLM may explain simulation output, but not secretly create the numeric
output" -- see app/simulation/engine.py).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

if TYPE_CHECKING:
    from app.models.career_twin import CareerTwinSnapshot
    from app.models.student import TargetRole

ACTIVITY_TYPES = [
    "practice_problems",
    "mock_interview",
    "reading",
    "project",
    "mixed",
]


class ExperimentScenario(UUIDPKMixin, Base):
    __tablename__ = "experiment_scenarios"

    student_profile_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("target_roles.id", ondelete="SET NULL"), nullable=True
    )
    time_horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    # list[{"skill_name": str, "activity_type": str, "hours": float}]
    allocations: Mapped[list] = mapped_column(JSONBType(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    target_role: Mapped["TargetRole | None"] = relationship()
    result: Mapped["ExperimentResult | None"] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", uselist=False
    )


class ExperimentResult(UUIDPKMixin, Base):
    __tablename__ = "experiment_results"

    scenario_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("experiment_scenarios.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    engine_version: Mapped[str] = mapped_column(String(30), nullable=False)
    baseline_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("career_twin_snapshots.id", ondelete="SET NULL"), nullable=True
    )
    current_overall_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    simulated_overall_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    overall_score_delta: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    overall_confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    overall_uncertainty: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    # list[{"component_type","current_score","simulated_score","delta","confidence","uncertainty","assumptions":[...]}]
    component_changes: Mapped[list] = mapped_column(JSONBType(), nullable=False)
    assumptions: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    evidence_used: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    # list[{"factor","label","swing"}] -- see app/simulation/engine.py::compute_sensitivity.
    sensitivity: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    # Opportunity-cost callouts (see compute_opportunity_cost_notes) -- never
    # blank when this plan actually spends hours on an already-strong component.
    waste_notes: Mapped[list] = mapped_column(JSONBType(), default=list, nullable=False)
    # Deterministic-engine-produced explanation is always present; the
    # provider-backed prose gloss (never the numbers) may replace/augment it.
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)

    scenario: Mapped["ExperimentScenario"] = relationship(back_populates="result")
    baseline_snapshot: Mapped["CareerTwinSnapshot | None"] = relationship()
