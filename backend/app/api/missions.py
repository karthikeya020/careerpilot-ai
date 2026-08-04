import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.base import utcnow
from app.models.mission import MISSION_STATUS_COMPLETED, LearningMission
from app.models.student import StudentProfile
from app.schemas.mission import LearningMissionOut
from app.services.mission_service import get_active_mission

router = APIRouter(prefix="/missions", tags=["missions"])


@router.get("/active", response_model=LearningMissionOut)
def get_active(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LearningMission:
    mission = get_active_mission(db, student_profile.id)
    if mission is None:
        raise NotFoundError("No active mission yet. Complete onboarding to generate one.")
    return mission


@router.get("", response_model=list[LearningMissionOut])
def list_missions(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[LearningMission]:
    return list(
        db.scalars(
            select(LearningMission)
            .where(LearningMission.student_profile_id == student_profile.id)
            .order_by(LearningMission.created_at.desc())
        ).all()
    )


@router.post("/{mission_id}/complete", response_model=LearningMissionOut)
def complete_mission(
    mission_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LearningMission:
    mission = db.scalar(
        select(LearningMission).where(
            LearningMission.id == mission_id, LearningMission.student_profile_id == student_profile.id
        )
    )
    if mission is None:
        raise NotFoundError("Mission not found")
    mission.status = MISSION_STATUS_COMPLETED
    mission.completed_at = utcnow()
    db.commit()
    db.refresh(mission)
    return mission
