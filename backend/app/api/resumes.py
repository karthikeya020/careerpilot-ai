import uuid

from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.resume import Resume
from app.models.student import StudentProfile
from app.schemas.resume import ResumeOut, ResumeSummaryOut
from app.services.resume_service import (
    activate_resume,
    get_latest_resume,
    list_resumes,
    process_resume,
)

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("", response_model=ResumeOut, status_code=201)
async def upload_resume(
    file: UploadFile,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Resume:
    content = await file.read()
    return process_resume(db, student_profile, file, content)


@router.get("/me", response_model=ResumeOut)
def get_my_latest_resume(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Resume:
    resume = get_latest_resume(db, student_profile.id)
    if resume is None:
        raise NotFoundError("No resume has been uploaded yet.")
    return resume


@router.get("", response_model=list[ResumeSummaryOut])
def get_resume_history(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ResumeSummaryOut]:
    resumes = list_resumes(db, student_profile.id)
    return [
        ResumeSummaryOut(
            id=r.id,
            original_filename=r.original_filename,
            file_size=r.file_size,
            parsing_status=r.parsing_status,
            uploaded_at=r.uploaded_at,
            parsed_at=r.parsed_at,
            is_active=r.is_active,
            superseded_at=r.superseded_at,
            skill_count=len(r.resume_skills),
        )
        for r in resumes
    ]


@router.post("/{resume_id}/activate", response_model=ResumeOut)
def activate_resume_version(
    resume_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> Resume:
    return activate_resume(db, student_profile, resume_id)
