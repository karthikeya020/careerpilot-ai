from fastapi import APIRouter, Depends

from app.core.deps import get_current_student_profile
from app.models.student import StudentProfile
from app.schemas.student import StudentProfileOut

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=StudentProfileOut)
def get_my_profile(student_profile: StudentProfile = Depends(get_current_student_profile)) -> StudentProfile:
    return student_profile
