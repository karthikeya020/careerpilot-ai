from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.models.resource import Resource
from app.models.student import StudentProfile
from app.schemas.resource import ResourceOut, ResourceRecommendationOut
from app.services import resource_service

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=list[ResourceOut])
def list_resources(
    concept: str | None = None,
    skill: str | None = None,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[Resource]:
    return resource_service.list_resources(db, concept_slug=concept, skill_name=skill)


@router.get("/recommendations", response_model=ResourceRecommendationOut)
def recommend_resources(
    concept: str,
    minutes: int = 30,
    max_difficulty: int = 5,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> ResourceRecommendationOut:
    resources, summary, confidence = resource_service.recommend_resources(
        db, concept_slug=concept, available_minutes=minutes, max_difficulty=max_difficulty
    )
    return ResourceRecommendationOut(
        resources=[ResourceOut.model_validate(r) for r in resources],
        reasoning_summary=summary,
        confidence=confidence,
    )
