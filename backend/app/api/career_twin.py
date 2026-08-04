from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.scoring import build_career_twin_snapshot_out
from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.career_twin import CareerTwinSnapshot
from app.models.student import StudentProfile
from app.schemas.career_twin import CareerTwinSnapshotOut

router = APIRouter(prefix="/career-twin", tags=["career-twin"])


@router.get("", response_model=CareerTwinSnapshotOut)
def get_latest_snapshot(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> CareerTwinSnapshotOut:
    snapshot = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    if snapshot is None:
        raise NotFoundError("No Career Twin snapshot yet. Complete onboarding to generate one.")
    return build_career_twin_snapshot_out(db, snapshot)


@router.get("/history", response_model=list[CareerTwinSnapshotOut])
def get_snapshot_history(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[CareerTwinSnapshotOut]:
    snapshots = db.scalars(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    ).all()
    return [build_career_twin_snapshot_out(db, s) for s in snapshots]
