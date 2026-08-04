"""Career Experiment Lab orchestration: turns a scenario definition into a
persisted, deterministic simulation result. The numeric work is entirely
delegated to `app/simulation/engine.py`; this module's only extra step is
asking `ExperimentExplainerAgent` to restate the already-computed numbers in
readable prose (never to compute them) and persisting both the scenario and
its result together.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.experiment_explainer_agent import (
    ComponentChangeSummary,
    ExperimentExplainerAgent,
    ExperimentExplainerInput,
)
from app.core.errors import NotFoundError
from app.models.experiment import ExperimentResult, ExperimentScenario
from app.models.student import StudentProfile
from app.simulation.engine import AllocationInput, SimulationResult, simulate_scenario

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
