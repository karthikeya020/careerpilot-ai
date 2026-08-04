from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile, get_current_user
from app.core.errors import UnauthorizedError
from app.core.security import verify_password
from app.models.student import StudentProfile
from app.models.user import User
from app.schemas.responsible_ai import AudioDeletionResultOut, ResponsibleAIOverviewOut
from app.services import responsible_ai_service

router = APIRouter(prefix="/responsible-ai", tags=["responsible-ai"])


class DeleteAccountRequest(BaseModel):
    password: str


@router.get("/overview", response_model=ResponsibleAIOverviewOut)
def get_overview(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> dict:
    return responsible_ai_service.get_overview(db, student_profile)


@router.get("/export")
def export_my_data(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> dict:
    return responsible_ai_service.export_student_data(db, student_profile)


@router.delete("/interview-audio", response_model=AudioDeletionResultOut)
def delete_interview_audio(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> AudioDeletionResultOut:
    deleted = responsible_ai_service.delete_interview_audio(db, student_profile)
    return AudioDeletionResultOut(deleted_count=deleted)


@router.delete("/account", status_code=204)
def delete_my_account(
    payload: DeleteAccountRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(payload.password, user.password_hash):
        raise UnauthorizedError("Incorrect password.")
    responsible_ai_service.delete_account(db, user.id)
