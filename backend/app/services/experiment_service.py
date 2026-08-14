"""Career Experiment Lab orchestration: turns a scenario definition into a
persisted, deterministic simulation result. The numeric work is entirely
delegated to `app/simulation/engine.py`; this module's only extra step is
asking `ExperimentExplainerAgent` to restate the already-computed numbers in
readable prose (never to compute them) and persisting both the scenario and
its result together.
"""

import uuid
from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.experiment_explainer_agent import (
    ComponentChangeSummary,
    ExperimentExplainerAgent,
    ExperimentExplainerInput,
)
from app.core.errors import NotFoundError
from app.models.career_twin import CareerTwinSnapshot
from app.models.experiment import ExperimentResult, ExperimentScenario
from app.models.student import StudentProfile
from app.simulation.engine import (
    AllocationInput,
    SimulationResult,
    compute_opportunity_cost_notes,
    compute_sensitivity,
    simulate_scenario,
)
from app.simulation.inverse import (
    CalendarPlan,
    InverseSolveResult,
    MarginalGainPoint,
    build_calendar_plan,
    marginal_gain_curve,
    reorder_by_prerequisites,
    solve_for_target,
)

_MAX_ALLOCATIONS_PER_SCENARIO = 8


def run_scenario(
    db: Session,
    student_profile: StudentProfile,
    name: str,
    allocations: list[dict],
    target_role_id: uuid.UUID | None = None,
    time_horizon_days: int = 30,
) -> ExperimentScenario:
    if not allocations:
        raise ValueError("A scenario needs at least one skill/hours allocation.")
    if len(allocations) > _MAX_ALLOCATIONS_PER_SCENARIO:
        raise ValueError(f"A scenario can have at most {_MAX_ALLOCATIONS_PER_SCENARIO} allocations.")

    scenario = ExperimentScenario(
        student_profile_id=student_profile.id,
        name=name,
        target_role_id=target_role_id,
        time_horizon_days=time_horizon_days,
        allocations=allocations,
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)

    allocation_inputs = [
        AllocationInput(skill_name=a["skill_name"], activity_type=a["activity_type"], hours=float(a["hours"]))
        for a in allocations
    ]
    result = simulate_scenario(db, student_profile, allocation_inputs, target_role_id)
    result.sensitivity = compute_sensitivity(db, student_profile, allocation_inputs, target_role_id, result)
    result.waste_notes = compute_opportunity_cost_notes(result.component_changes)
    _persist_result(db, scenario, result)
    db.refresh(scenario)
    return scenario


def _persist_result(db: Session, scenario: ExperimentScenario, result: SimulationResult) -> ExperimentResult:
    explainer = ExperimentExplainerAgent()
    explainer_output, _latency = explainer.safe_run(
        ExperimentExplainerInput(
            component_changes=[
                ComponentChangeSummary(
                    component_type=c.component_type,
                    current_score=c.current_score,
                    simulated_score=c.simulated_score,
                    delta=c.delta,
                )
                for c in result.component_changes
            ],
            overall_current_score=result.current_overall_score,
            overall_simulated_score=result.simulated_overall_score,
            overall_delta=result.overall_score_delta,
            assumptions=result.assumptions,
        )
    )
    explanation = explainer_output.narrative if explainer_output.status == "completed" else result.explanation

    row = ExperimentResult(
        scenario_id=scenario.id,
        engine_version=result.engine_version,
        baseline_snapshot_id=result.baseline_snapshot_id,
        current_overall_score=result.current_overall_score,
        simulated_overall_score=result.simulated_overall_score,
        overall_score_delta=result.overall_score_delta,
        overall_confidence=result.overall_confidence,
        overall_uncertainty=result.overall_uncertainty,
        component_changes=[
            {
                "component_type": c.component_type,
                "current_score": c.current_score,
                "simulated_score": c.simulated_score,
                "delta": c.delta,
                "confidence": c.confidence,
                "uncertainty": c.uncertainty,
                "assumptions": c.assumptions,
                "evidence_used": c.evidence_used,
            }
            for c in result.component_changes
        ],
        assumptions=result.assumptions,
        evidence_used=result.evidence_used,
        sensitivity=[{"factor": s.factor, "label": s.label, "swing": s.swing} for s in result.sensitivity],
        waste_notes=result.waste_notes,
        explanation=explanation,
        disclaimer=result.disclaimer,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_scenario(db: Session, scenario_id: uuid.UUID) -> ExperimentScenario | None:
    return db.get(ExperimentScenario, scenario_id)


def list_scenarios(db: Session, student_profile_id: uuid.UUID, limit: int = 20) -> list[ExperimentScenario]:
    return list(
        db.scalars(
            select(ExperimentScenario)
            .where(ExperimentScenario.student_profile_id == student_profile_id)
            .order_by(ExperimentScenario.created_at.desc())
            .limit(limit)
        ).all()
    )


def compare_scenarios(db: Session, student_profile_id: uuid.UUID, scenario_ids: list[uuid.UUID]) -> list[ExperimentScenario]:
    scenarios = []
    for scenario_id in scenario_ids:
        scenario = get_scenario(db, scenario_id)
        if scenario is None or scenario.student_profile_id != student_profile_id:
            raise NotFoundError(f"Scenario {scenario_id} not found.")
        scenarios.append(scenario)
    return scenarios


@dataclass
class TargetPlan:
    solve: InverseSolveResult
    calendar: CalendarPlan
    marginal_gain_curve: list[MarginalGainPoint]


def plan_target(
    db: Session,
    student_profile: StudentProfile,
    target_component: str,
    target_score: float,
    candidate_skill_names: list[str],
    weekly_hours: float = 10.0,
    deadline: date | None = None,
    activity_type: str = "practice_problems",
) -> TargetPlan:
    """Inverse mode: "I need X readiness by date Y, cheapest path?" --
    solves backwards from the target (solve_for_target), reorders the plan
    using real DEPENDS_ON prerequisite edges (reorder_by_prerequisites), then
    shapes it into a calendar respecting a real weekly-hours budget and
    deadline (build_calendar_plan). Same engine as forward simulation, run
    as a search rather than a single evaluation."""
    solve = solve_for_target(
        db, student_profile, target_component, target_score, candidate_skill_names, weekly_hours, activity_type
    )
    ordered_plan = reorder_by_prerequisites(db, solve.plan)
    solve.plan = ordered_plan
    calendar = build_calendar_plan(ordered_plan, weekly_hours, deadline=deadline)
    curve = marginal_gain_curve(activity_type)
    return TargetPlan(solve=solve, calendar=calendar, marginal_gain_curve=curve)


@dataclass
class PredictionAccuracy:
    status: str  # "measured" | "no_new_evidence_yet" | "no_baseline"
    predicted_delta: float | None = None
    actual_delta: float | None = None
    absolute_error: float | None = None
    days_elapsed: int | None = None
    baseline_snapshot_version: int | None = None
    current_snapshot_version: int | None = None
    message: str = ""


def evaluate_prediction_accuracy(db: Session, student_profile: StudentProfile, scenario_id: uuid.UUID) -> PredictionAccuracy:
    """Every scenario a student runs is already persisted permanently
    (ExperimentScenario/ExperimentResult) -- this is the bridge to Research
    Lab: compare what a scenario predicted against what actually happened,
    by diffing the scenario's baseline snapshot against the student's
    current real Career Twin snapshot. Makes the Experiment Lab
    self-correcting instead of speculative; never invents an "actual"
    number before real evidence exists."""
    scenario = get_scenario(db, scenario_id)
    if scenario is None or scenario.student_profile_id != student_profile.id:
        raise NotFoundError("Scenario not found.")

    result = scenario.result
    if result is None or result.baseline_snapshot_id is None or result.overall_score_delta is None:
        return PredictionAccuracy(status="no_baseline", message="This scenario has no baseline snapshot to compare against.")

    baseline = db.get(CareerTwinSnapshot, result.baseline_snapshot_id)
    latest = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    if baseline is None or latest is None or baseline.overall_score is None:
        return PredictionAccuracy(status="no_baseline", message="This scenario has no baseline snapshot to compare against.")

    if latest.id == baseline.id:
        return PredictionAccuracy(
            status="no_new_evidence_yet",
            predicted_delta=float(result.overall_score_delta),
            message="No Career Twin update has happened since this scenario was run -- nothing to compare yet.",
        )

    actual_delta = (
        round(float(latest.overall_score) - float(baseline.overall_score), 4) if latest.overall_score is not None else None
    )
    if actual_delta is None:
        return PredictionAccuracy(
            status="no_new_evidence_yet",
            predicted_delta=float(result.overall_score_delta),
            message="Your Career Twin doesn't have a scored overall readiness yet -- nothing to compare.",
        )

    predicted_delta = float(result.overall_score_delta)
    return PredictionAccuracy(
        status="measured",
        predicted_delta=predicted_delta,
        actual_delta=actual_delta,
        absolute_error=round(abs(predicted_delta - actual_delta), 4),
        days_elapsed=(latest.created_at - scenario.created_at).days,
        baseline_snapshot_version=baseline.version,
        current_snapshot_version=latest.version,
        message=f"Predicted {predicted_delta:+.2%}, actual {actual_delta:+.2%} so far.",
    )
