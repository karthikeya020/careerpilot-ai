from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.models.student import StudentProfile
from app.schemas.onboarding import OnboardingRequest
from app.schemas.student import StudentProfileOut
from app.services.onboarding_service import complete_onboarding

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


@router.post("", response_model=StudentProfileOut)
def submit_onboarding(
    payload: OnboardingRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> StudentProfile:
    return complete_onboarding(db, student_profile, payload)
