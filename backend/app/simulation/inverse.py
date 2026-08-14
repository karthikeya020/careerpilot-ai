"""Inverse-mode planning: "I need Data Analyst readiness at 80% by December
15 -- what's the cheapest path?" Solves backwards from a target instead of
forwards from a fixed hour input, using the exact same per-allocation
diminishing-returns formula as `simulate_scenario` (app/simulation/engine.py)
-- run as a greedy search over allocations rather than a single evaluation.
No new numeric model: every marginal-gain calculation below is the identical
math the forward simulator already uses, just re-evaluated at each search
step. (Constitution rule 1/10: no invented numbers, no new unvalidated path.)

Graph-aware ordering (`reorder_by_prerequisites`) and calendar-shaping
(`build_calendar_plan`) are pure presentation/scheduling logic over the
search's own output -- they never change a projected score, only the order
and weekly grouping in which the plan is presented.
"""

import math
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Concept, ConceptDependency
from app.models.career_twin import CareerTwinSnapshot
from app.models.student import StudentProfile
from app.simulation.engine import (
    ACTIVITY_EFFECTIVENESS,
    DEFAULT_ACTIVITY_EFFECTIVENESS,
    DISCLAIMER,
    HOURS_DECAY_CONSTANT,
    MAX_GAIN_PER_ALLOCATION,
    NEUTRAL_SCORE_PRIOR,
    SIMULATION_ENGINE_VERSION,
    _clamp,
    _current_components,
    _dependents_bonus,
    _historical_response_multiplier,
    _resolve_skill,
    _role_importance,
)

_INVERSE_HOUR_STEP = 2.0
_INVERSE_MAX_HOURS = 400.0
_INVERSE_MIN_MARGINAL_GAIN = 0.0005


@dataclass
class AllocationPlanItem:
    skill_name: str
    activity_type: str
    hours: float
    order_rank: int
    scheduling_reason: str | None = None


@dataclass
class InverseSolveResult:
    engine_version: str
    target_component: str
    target_score: float
    baseline_score: float | None
    reached_target: bool
    plan: list[AllocationPlanItem]
    total_hours: float
    weeks_to_complete: int | None
    assumptions: list[str] = field(default_factory=list)
    disclaimer: str = DISCLAIMER


def solve_for_target(
    db: Session,
    student_profile: StudentProfile,
    target_component: str,
    target_score: float,
    candidate_skill_names: list[str],
    weekly_hours: float = 10.0,
    activity_type: str = "practice_problems",
) -> InverseSolveResult:
    baseline = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    current = _current_components(baseline)
    baseline_score = current.get(target_component, {}).get("score")
    running_score = baseline_score if baseline_score is not None else NEUTRAL_SCORE_PRIOR

    if running_score >= target_score:
        return InverseSolveResult(
            engine_version=SIMULATION_ENGINE_VERSION,
            target_component=target_component,
            target_score=target_score,
            baseline_score=baseline_score,
            reached_target=True,
            plan=[],
            total_hours=0.0,
            weeks_to_complete=0,
            assumptions=[f"Already at or above the {target_score:.0%} target -- no additional hours needed."],
        )

    effectiveness = ACTIVITY_EFFECTIVENESS.get(activity_type, DEFAULT_ACTIVITY_EFFECTIVENESS)

    candidates: list[dict] = []
    for name in candidate_skill_names:
        skill = _resolve_skill(db, name)
        if skill is None:
            continue
        role_importance, _has_jd = _role_importance(db, student_profile.id, skill)
        role_factor = 0.5 + 0.5 * role_importance
        dependents_bonus = _dependents_bonus(db, skill)
        historical_multiplier, _has_history = _historical_response_multiplier(db, student_profile.id, target_component)
        candidates.append(
            {
                "skill": skill,
                "role_factor": role_factor,
                "dependents_bonus": dependents_bonus,
                "historical_multiplier": historical_multiplier,
                "hours": 0.0,
            }
        )

    if not candidates:
        return InverseSolveResult(
            engine_version=SIMULATION_ENGINE_VERSION,
            target_component=target_component,
            target_score=target_score,
            baseline_score=baseline_score,
            reached_target=False,
            plan=[],
            total_hours=0.0,
            weeks_to_complete=None,
            assumptions=["None of the candidate skills were recognized in the skill taxonomy -- no plan could be built."],
        )

    total_hours = 0.0
    while running_score < target_score and total_hours < _INVERSE_MAX_HOURS:
        best_candidate = None
        best_marginal_gain = -1.0
        headroom_factor = 0.3 + 0.7 * (1 - running_score)
        for candidate in candidates:
            h0, h1 = candidate["hours"], candidate["hours"] + _INVERSE_HOUR_STEP
            raw0 = MAX_GAIN_PER_ALLOCATION * (1 - math.exp(-h0 / HOURS_DECAY_CONSTANT)) * effectiveness
            raw1 = MAX_GAIN_PER_ALLOCATION * (1 - math.exp(-h1 / HOURS_DECAY_CONSTANT)) * effectiveness
            marginal_gain = (
                (raw1 - raw0)
                * headroom_factor
                * candidate["role_factor"]
                * candidate["dependents_bonus"]
                * candidate["historical_multiplier"]
            )
            if marginal_gain > best_marginal_gain:
                best_marginal_gain = marginal_gain
                best_candidate = candidate

        if best_candidate is None or best_marginal_gain < _INVERSE_MIN_MARGINAL_GAIN:
            break
        best_candidate["hours"] += _INVERSE_HOUR_STEP
        running_score = _clamp(running_score + best_marginal_gain)
        total_hours += _INVERSE_HOUR_STEP

    reached = running_score >= target_score
    used = [c for c in candidates if c["hours"] > 0]
    used.sort(key=lambda c: -c["hours"])
    plan = [
        AllocationPlanItem(skill_name=c["skill"].name, activity_type=activity_type, hours=c["hours"], order_rank=i + 1)
        for i, c in enumerate(used)
    ]
    weeks_to_complete = math.ceil(total_hours / weekly_hours) if weekly_hours > 0 and total_hours > 0 else (0 if total_hours == 0 else None)

    assumptions = [
        (
            f"Searched in {_INVERSE_HOUR_STEP:.0f}-hour increments across {len(candidates)} candidate skill(s), "
            "always allocating the next block to whichever skill currently offers the best marginal readiness "
            "gain per hour -- the same diminishing-returns formula the forward simulator uses, run as a search "
            "instead of a single evaluation."
        ),
    ]
    if not reached:
        assumptions.append(
            f"Target not reached within a {int(_INVERSE_MAX_HOURS)}-hour search cap -- marginal gains from these "
            f"candidate skills plateaued before reaching {target_score:.0%}. Add more candidate skills or accept "
            "a lower target; this is an honest infeasibility signal, not a rounding artifact."
        )

    return InverseSolveResult(
        engine_version=SIMULATION_ENGINE_VERSION,
        target_component=target_component,
        target_score=target_score,
        baseline_score=baseline_score,
        reached_target=reached,
        plan=plan,
        total_hours=total_hours,
        weeks_to_complete=weeks_to_complete,
        assumptions=assumptions,
    )


def reorder_by_prerequisites(db: Session, plan: list[AllocationPlanItem]) -> list[AllocationPlanItem]:
    """Front-loads plan items whose skill is a prerequisite (DEPENDS_ON,
    direct edges only) for another skill already in the plan -- a naive
    planner would happily schedule the dependent skill first even while its
    prerequisite is unaddressed; this uses the real concept-dependency graph
    to say explicitly why the order changed.

    A skill commonly maps to *several* concepts (e.g. "Data Structures"
    covers Arrays & Strings, Linked Lists, Stacks & Queues, Trees & Graphs),
    so this considers every concept under each candidate skill rather than
    one arbitrary representative -- a dependency between any concept pair
    across two different candidate skills is enough to flag the ordering."""
    if not plan:
        return plan

    skill_names = {item.skill_name for item in plan}
    concepts = db.scalars(select(Concept).where(Concept.skill_id.is_not(None))).all()

    concept_id_to_skill_name: dict[uuid.UUID, str] = {}
    for concept in concepts:
        if concept.skill is not None and concept.skill.name in skill_names:
            concept_id_to_skill_name[concept.id] = concept.skill.name

    plan_concept_ids = set(concept_id_to_skill_name.keys())
    if not plan_concept_ids:
        return plan

    dep_rows = db.scalars(
        select(ConceptDependency).where(
            ConceptDependency.concept_id.in_(plan_concept_ids) & ConceptDependency.depends_on_id.in_(plan_concept_ids)
        )
    ).all()

    # dependents_of[prerequisite_skill] = other candidate skills whose
    # concepts directly depend on a concept belonging to prerequisite_skill.
    dependents_of: dict[str, set[str]] = {}
    for dep in dep_rows:
        dependent_skill = concept_id_to_skill_name.get(dep.concept_id)
        prerequisite_skill = concept_id_to_skill_name.get(dep.depends_on_id)
        if dependent_skill and prerequisite_skill and dependent_skill != prerequisite_skill:
            dependents_of.setdefault(prerequisite_skill, set()).add(dependent_skill)

    def priority_key(item: AllocationPlanItem) -> tuple:
        dependent_count = len(dependents_of.get(item.skill_name, ()))
        return (-dependent_count, -item.hours)

    ordered = sorted(plan, key=priority_key)
    reordered: list[AllocationPlanItem] = []
    for i, item in enumerate(ordered):
        dependents = dependents_of.get(item.skill_name, set())
        reason = (
            f"Scheduled first because {', '.join(sorted(dependents))} directly depend"
            f"{'s' if len(dependents) == 1 else ''} on it."
            if dependents
            else None
        )
        reordered.append(
            AllocationPlanItem(
                skill_name=item.skill_name,
                activity_type=item.activity_type,
                hours=item.hours,
                order_rank=i + 1,
                scheduling_reason=reason,
            )
        )
    return reordered


@dataclass
class MarginalGainPoint:
    hours: float
    marginal_gain: float
    cumulative_gain: float


def marginal_gain_curve(activity_type: str = "practice_problems", max_hours: float = 40.0, step: float = 2.0) -> list[MarginalGainPoint]:
    """The raw per-hour diminishing-returns curve (headroom/role/history
    factors excluded -- those are per-student/per-skill multipliers on top
    of this same base curve) so the frontend can show *why* the 30th hour
    visibly returns less than the 5th."""
    effectiveness = ACTIVITY_EFFECTIVENESS.get(activity_type, DEFAULT_ACTIVITY_EFFECTIVENESS)
    points: list[MarginalGainPoint] = []
    previous_raw = 0.0
    hours = 0.0
    while hours < max_hours:
        hours += step
        raw = MAX_GAIN_PER_ALLOCATION * (1 - math.exp(-hours / HOURS_DECAY_CONSTANT)) * effectiveness
        points.append(MarginalGainPoint(hours=hours, marginal_gain=round(raw - previous_raw, 5), cumulative_gain=round(raw, 5)))
        previous_raw = raw
    return points


@dataclass
class CalendarWeek:
    week_number: int
    start_date: str
    items: list[dict] = field(default_factory=list)
    total_hours: float = 0.0


@dataclass
class CalendarPlan:
    weeks: list[CalendarWeek]
    weekly_hours_budget: float
    total_hours: float
    weeks_needed: int
    deadline: str | None = None
    fits_deadline: bool | None = None
    feasibility_note: str | None = None


def build_calendar_plan(
    plan: list[AllocationPlanItem], weekly_hours: float, start: date | None = None, deadline: date | None = None
) -> CalendarPlan:
    start = start or date.today()
    weekly_hours = max(1.0, weekly_hours)
    total_hours = sum(item.hours for item in plan)
    weeks_needed = math.ceil(total_hours / weekly_hours) if total_hours > 0 else 0

    remaining = [{"skill_name": i.skill_name, "activity_type": i.activity_type, "hours": i.hours} for i in plan]
    weeks: list[CalendarWeek] = []
    week_number = 1
    while remaining:
        week = CalendarWeek(week_number=week_number, start_date=(start + timedelta(weeks=week_number - 1)).isoformat())
        budget_left = weekly_hours
        while remaining and budget_left > 0:
            item = remaining[0]
            take = min(item["hours"], budget_left)
            week.items.append({"skill_name": item["skill_name"], "activity_type": item["activity_type"], "hours": round(take, 2)})
            week.total_hours = round(week.total_hours + take, 2)
            budget_left -= take
            item["hours"] -= take
            if item["hours"] <= 1e-9:
                remaining.pop(0)
        weeks.append(week)
        week_number += 1
        if week_number > 260:  # 5-year hard stop, defensive only
            break

    fits_deadline = None
    feasibility_note = None
    if deadline is not None:
        available_weeks = max(0, (deadline - start).days // 7)
        fits_deadline = weeks_needed <= available_weeks
        if not fits_deadline:
            feasibility_note = (
                f"This plan needs {weeks_needed} week(s) at {weekly_hours:.0f}h/week, but only {available_weeks} "
                f"week(s) remain before {deadline.isoformat()}. Increase weekly hours, narrow the target, or move the deadline."
            )

    return CalendarPlan(
        weeks=weeks,
        weekly_hours_budget=weekly_hours,
        total_hours=round(total_hours, 2),
        weeks_needed=weeks_needed,
        deadline=deadline.isoformat() if deadline else None,
        fits_deadline=fits_deadline,
        feasibility_note=feasibility_note,
    )
