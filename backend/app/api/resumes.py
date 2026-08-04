from fastapi import APIRouter, Depends, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.resume import Resume
from app.models.student import StudentProfile
from app.schemas.resume import ResumeOut
from app.services.resume_service import get_latest_resume, process_resume

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
