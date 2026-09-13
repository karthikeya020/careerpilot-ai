from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.models.student import StudentProfile
from app.schemas.github_profile import GithubProfileOut
from app.schemas.leetcode_profile import LeetCodeProfileOut
from app.schemas.student import (
    SetCameraConsentRequest,
    StudentProfileOut,
    StudentProfileUpdateRequest,
)
from app.services import github_profile_service, leetcode_profile_service
from app.services.student_service import set_camera_consent, update_profile_details

router = APIRouter(prefix="/students", tags=["students"])


@router.get("/me", response_model=StudentProfileOut)
def get_my_profile(student_profile: StudentProfile = Depends(get_current_student_profile)) -> StudentProfile:
    return student_profile


@router.patch("/me", response_model=StudentProfileOut)
def update_my_profile(
    payload: StudentProfileUpdateRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> StudentProfile:
    return update_profile_details(db, student_profile, payload)


@router.get("/me/github-profile", response_model=GithubProfileOut)
def get_my_github_profile(student_profile: StudentProfile = Depends(get_current_student_profile)) -> GithubProfileOut:
    if not student_profile.github_username:
        return GithubProfileOut(status="not_configured")
    return github_profile_service.fetch_profile(student_profile.github_username)


@router.get("/me/leetcode-profile", response_model=LeetCodeProfileOut)
def get_my_leetcode_profile(
    student_profile: StudentProfile = Depends(get_current_student_profile),
) -> LeetCodeProfileOut:
    if not student_profile.leetcode_username:
        return LeetCodeProfileOut(status="not_configured")
    return leetcode_profile_service.fetch_profile(student_profile.leetcode_username)


@router.put("/me/camera-consent", status_code=204)
def set_my_camera_consent(
    payload: SetCameraConsentRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> None:
    set_camera_consent(db, student_profile, payload.enabled)
