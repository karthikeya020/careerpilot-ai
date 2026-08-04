import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.models.job_description import JD_SOURCE_PASTED, JobDescription
from app.models.student import StudentProfile
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionOut, MatchResultOut
from app.services.job_description_service import (
    MatchResult,
    create_job_description,
    get_job_description_or_404,
    get_job_descriptions,
    get_match,
)

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.post("", response_model=JobDescriptionOut, status_code=201)
def add_job_description(
    payload: JobDescriptionCreate,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> JobDescription:
    return create_job_description(
        db, student_profile, payload.title, payload.company, payload.raw_text, JD_SOURCE_PASTED
    )


@router.get("", response_model=list[JobDescriptionOut])
def list_job_descriptions(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[JobDescription]:
    return get_job_descriptions(db, student_profile.id)


@router.get("/{job_description_id}", response_model=JobDescriptionOut)
def get_job_description(
    job_description_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> JobDescription:
    return get_job_description_or_404(db, student_profile.id, job_description_id)


@router.get("/{job_description_id}/match", response_model=MatchResultOut)
def get_job_description_match(
    job_description_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> MatchResult:
    jd = get_job_description_or_404(db, student_profile.id, job_description_id)
    return get_match(db, student_profile, jd)
