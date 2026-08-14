import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError, UnprocessableError
from app.models.experiment import ACTIVITY_TYPES, ExperimentScenario
from app.models.student import StudentProfile
from app.schemas.experiment import (
    ExperimentScenarioOut,
    PredictionAccuracyOut,
    StartExperimentRequest,
    TargetPlanOut,
    TargetPlanRequest,
)
from app.services import experiment_service

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("/activity-types")
def list_activity_types() -> list[str]:
    return ACTIVITY_TYPES


def _get_owned_scenario(db: Session, scenario_id: uuid.UUID, student_profile: StudentProfile) -> ExperimentScenario:
    scenario = experiment_service.get_scenario(db, scenario_id)
    if scenario is None or scenario.student_profile_id != student_profile.id:
        raise NotFoundError("Scenario not found.")
    return scenario


@router.post("/scenarios", response_model=ExperimentScenarioOut, status_code=201)
def run_scenario(
    payload: StartExperimentRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> ExperimentScenario:
    try:
        return experiment_service.run_scenario(
            db,
            student_profile,
            name=payload.name,
            allocations=[a.model_dump() for a in payload.allocations],
            target_role_id=payload.target_role_id,
            time_horizon_days=payload.time_horizon_days,
        )
    except ValueError as exc:
        raise UnprocessableError(str(exc)) from exc


@router.get("/scenarios", response_model=list[ExperimentScenarioOut])
def list_scenarios(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ExperimentScenario]:
    return experiment_service.list_scenarios(db, student_profile.id)


@router.get("/scenarios/{scenario_id}", response_model=ExperimentScenarioOut)
def get_scenario(
    scenario_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> ExperimentScenario:
    return _get_owned_scenario(db, scenario_id, student_profile)


@router.get("/compare", response_model=list[ExperimentScenarioOut])
def compare_scenarios(
    scenario_ids: list[uuid.UUID] = Query(...),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ExperimentScenario]:
    return experiment_service.compare_scenarios(db, student_profile.id, scenario_ids)


@router.post("/target-plan", response_model=TargetPlanOut)
def plan_target(
    payload: TargetPlanRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TargetPlanOut:
    """Inverse mode: "I need X readiness by date Y -- what's the cheapest
    path?" Solves backwards from the target instead of forwards from a fixed
    hour input."""
    result = experiment_service.plan_target(
        db,
        student_profile,
        target_component=payload.target_component,
        target_score=payload.target_score,
        candidate_skill_names=payload.candidate_skills,
        weekly_hours=payload.weekly_hours,
        deadline=payload.deadline,
        activity_type=payload.activity_type,
    )
    solve = result.solve
    return TargetPlanOut(
        engine_version=solve.engine_version,
        target_component=solve.target_component,
        target_score=solve.target_score,
        baseline_score=solve.baseline_score,
        reached_target=solve.reached_target,
        plan=[
            {
                "skill_name": p.skill_name,
                "activity_type": p.activity_type,
                "hours": p.hours,
                "order_rank": p.order_rank,
                "scheduling_reason": p.scheduling_reason,
            }
            for p in solve.plan
        ],
        total_hours=solve.total_hours,
        weeks_to_complete=solve.weeks_to_complete,
        assumptions=solve.assumptions,
        disclaimer=solve.disclaimer,
        calendar={
            "weeks": [
                {"week_number": w.week_number, "start_date": w.start_date, "items": w.items, "total_hours": w.total_hours}
                for w in result.calendar.weeks
            ],
            "weekly_hours_budget": result.calendar.weekly_hours_budget,
            "total_hours": result.calendar.total_hours,
            "weeks_needed": result.calendar.weeks_needed,
            "deadline": result.calendar.deadline,
            "fits_deadline": result.calendar.fits_deadline,
            "feasibility_note": result.calendar.feasibility_note,
        },
        marginal_gain_curve=[
            {"hours": p.hours, "marginal_gain": p.marginal_gain, "cumulative_gain": p.cumulative_gain}
            for p in result.marginal_gain_curve
        ],
    )


@router.get("/scenarios/{scenario_id}/prediction-accuracy", response_model=PredictionAccuracyOut)
def get_prediction_accuracy(
    scenario_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> PredictionAccuracyOut:
    accuracy = experiment_service.evaluate_prediction_accuracy(db, student_profile, scenario_id)
    return PredictionAccuracyOut(**accuracy.__dict__)
