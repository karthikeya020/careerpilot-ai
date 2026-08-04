import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError, UnprocessableError
from app.models.experiment import ACTIVITY_TYPES, ExperimentScenario
from app.models.student import StudentProfile
from app.schemas.experiment import ExperimentScenarioOut, StartExperimentRequest
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
