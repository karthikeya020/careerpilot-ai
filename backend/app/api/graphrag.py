import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.graphrag.neo4j_client import is_graph_available
from app.graphrag.schemas import GraphSnapshot, RootCauseResult
from app.graphrag.service import analyze_root_cause, get_concept_neighborhood
from app.models.student import StudentProfile

router = APIRouter(prefix="/graph", tags=["graphrag"])


@router.get("/health")
def graph_health() -> dict:
    return {"available": is_graph_available()}


@router.get("/concept/{slug}/neighborhood", response_model=GraphSnapshot)
def concept_neighborhood(
    slug: str,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> GraphSnapshot:
    return get_concept_neighborhood(db, slug)


@router.get("/root-cause/{question_id}", response_model=RootCauseResult)
def root_cause(
    question_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> RootCauseResult:
    return analyze_root_cause(db, student_profile, question_id)
