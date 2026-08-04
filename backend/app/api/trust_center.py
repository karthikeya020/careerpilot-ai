import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.care import CareExecution
from app.models.career_twin import CareerTwinSnapshot
from app.models.student import StudentProfile
from app.schemas.trust_center import (
    CareExecutionDetailOut,
    CareExecutionSummaryOut,
    TwinChangeExplanationOut,
)
from app.services import trust_center_service

router = APIRouter(prefix="/trust-center", tags=["trust-center"])


@router.get("/executions", response_model=list[CareExecutionSummaryOut])
def list_executions(
    limit: int = 20,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[CareExecution]:
    return trust_center_service.list_executions(db, student_profile.id, limit=limit)


@router.get("/executions/{execution_id}", response_model=CareExecutionDetailOut)
def get_execution(
    execution_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> CareExecution:
    execution = trust_center_service.get_execution_detail(db, execution_id)
    if execution is None or execution.student_profile_id != student_profile.id:
        raise NotFoundError("CARE execution not found.")
    return execution


@router.get("/twin-explanation/{snapshot_id}", response_model=TwinChangeExplanationOut)
def get_twin_explanation(
    snapshot_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TwinChangeExplanationOut:
    snapshot = db.get(CareerTwinSnapshot, snapshot_id)
    if snapshot is None or snapshot.student_profile_id != student_profile.id:
        raise NotFoundError("Career Twin snapshot not found.")
    return TwinChangeExplanationOut(**trust_center_service.explain_twin_change(db, snapshot))
