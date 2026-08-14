"""Time-to-target projection: using this student's own historical Career
Twin snapshots, project roughly how many weeks until a component reaches
the platform's "strong" readiness bar (70% -- the same threshold used
throughout the platform: component-score coloring, milestone detection,
GraphRAG's concept-mastery strong threshold). Always labeled an estimate,
never a guarantee, with a confidence band derived from the variance of this
student's own historical rate of change -- same discipline as the
Experiment Lab simulation engine (app/simulation/engine.py), just fed real
history instead of a what-if scenario. Fully deterministic, no model call
(Constitution rule 1/4).
"""

import math
import statistics
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.career_twin import ALL_COMPONENTS, STATUS_SCORED, CareerTwinSnapshot

TARGET_READINESS = 0.70
MIN_SNAPSHOTS_FOR_PROJECTION = 2
_MIN_ELAPSED_WEEKS = 1 / 7  # floor at one day, avoids a near-zero-time division blowing up the rate

PROJECTION_DISCLAIMER = (
    "Projected from this student's own historical rate of change -- a heuristic estimate, not a guarantee."
)

ProjectionStatus = str  # "already_at_target" | "insufficient_history" | "not_improving" | "projected"


@dataclass
class ComponentProjection:
    component_type: str
    current_score: float | None
    status: ProjectionStatus
    weeks_to_target: int | None = None
    weeks_to_target_low: int | None = None
    weeks_to_target_high: int | None = None
    weekly_rate: float | None = None
    note: str = ""


def _scored_history(snapshots: list[CareerTwinSnapshot], component_type: str) -> list[tuple]:
    points = []
    for snap in snapshots:
        component = next((c for c in snap.components if c.component_type == component_type), None)
        if component is not None and component.status == STATUS_SCORED and component.score is not None:
            points.append((snap.created_at, float(component.score)))
    return points


def project_time_to_target(
    db: Session, student_profile_id: uuid.UUID, target: float = TARGET_READINESS
) -> list[ComponentProjection]:
    snapshots = list(
        db.scalars(
            select(CareerTwinSnapshot)
            .where(CareerTwinSnapshot.student_profile_id == student_profile_id)
            .order_by(CareerTwinSnapshot.version.asc())
        ).all()
    )

    results: list[ComponentProjection] = []
    for component_type in ALL_COMPONENTS:
        points = _scored_history(snapshots, component_type)

        if not points:
            results.append(
                ComponentProjection(
                    component_type=component_type,
                    current_score=None,
                    status="insufficient_history",
                    note="No scored history yet for this component.",
                )
            )
            continue

        current_score = points[-1][1]
        if current_score >= target:
            results.append(
                ComponentProjection(
                    component_type=component_type,
                    current_score=current_score,
                    status="already_at_target",
                    note=f"Already at or above the {int(target * 100)}% target.",
                )
            )
            continue

        if len(points) < MIN_SNAPSHOTS_FOR_PROJECTION:
            results.append(
                ComponentProjection(
                    component_type=component_type,
                    current_score=current_score,
                    status="insufficient_history",
                    note=(
                        "Need at least two scored snapshots over time to project a rate -- not guessing "
                        "from a single data point."
                    ),
                )
            )
            continue

        first_ts, first_score = points[0]
        last_ts, last_score = points[-1]
        elapsed_weeks = max((last_ts - first_ts).total_seconds() / (7 * 86400), _MIN_ELAPSED_WEEKS)
        weekly_rate = (last_score - first_score) / elapsed_weeks

        per_step_rates: list[float] = []
        for i in range(1, len(points)):
            dt_weeks = max((points[i][0] - points[i - 1][0]).total_seconds() / (7 * 86400), _MIN_ELAPSED_WEEKS)
            per_step_rates.append((points[i][1] - points[i - 1][1]) / dt_weeks)
        rate_stdev = statistics.pstdev(per_step_rates) if len(per_step_rates) > 1 else 0.0

        if weekly_rate <= 0:
            results.append(
                ComponentProjection(
                    component_type=component_type,
                    current_score=current_score,
                    status="not_improving",
                    weekly_rate=round(weekly_rate, 4),
                    note="This component hasn't shown a positive trend yet, so a target date can't be honestly projected.",
                )
            )
            continue

        gap = target - current_score
        weeks = math.ceil(gap / weekly_rate)
        rate_low = max(weekly_rate - rate_stdev, weekly_rate * 0.3)
        rate_high = weekly_rate + rate_stdev
        weeks_low = math.ceil(gap / rate_high) if rate_high > 0 else weeks
        weeks_high = math.ceil(gap / rate_low) if rate_low > 0 else weeks

        results.append(
            ComponentProjection(
                component_type=component_type,
                current_score=current_score,
                status="projected",
                weeks_to_target=weeks,
                weeks_to_target_low=weeks_low,
                weeks_to_target_high=weeks_high,
                weekly_rate=round(weekly_rate, 4),
                note=(
                    f"Estimated from your own historical rate of {weekly_rate:.3f} points/week across "
                    f"{len(points)} scored snapshots. {PROJECTION_DISCLAIMER}"
                ),
            )
        )
    return results
