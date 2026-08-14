import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.graphrag.neo4j_client import is_graph_available
from app.graphrag.schemas import (
    ConceptInsightOut,
    GraphSnapshot,
    PracticeAnswerRequest,
    PracticeProgressOut,
    PracticeQuestionOut,
    RootCauseResult,
    StudentGraphOverviewOut,
)
from app.graphrag.service import analyze_root_cause, get_concept_insight, get_concept_neighborhood, get_student_graph_overview
from app.models.assessment import Concept, Question
from app.models.student import StudentProfile
from app.services import assessment_service

router = APIRouter(prefix="/graph", tags=["graphrag"])


def _practice_question_out(question: Question | None) -> PracticeQuestionOut | None:
    if question is None:
        return None
    return PracticeQuestionOut(
        id=question.id,
        question_type=question.question_type,
        prompt=question.prompt,
        options=question.options,
        difficulty=question.difficulty,
        difficulty_band=assessment_service.difficulty_band(question.difficulty),
    )


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


@router.get("/student-overview", response_model=StudentGraphOverviewOut)
def student_overview(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> StudentGraphOverviewOut:
    return get_student_graph_overview(db, student_profile)


@router.get("/concept/{slug}/insight", response_model=ConceptInsightOut)
def concept_insight(
    slug: str,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> ConceptInsightOut:
    insight = get_concept_insight(db, student_profile, slug)
    if insight is None:
        raise NotFoundError(f"Unknown concept '{slug}'.")
    return insight


@router.post("/practice/{concept_slug}/start", response_model=PracticeProgressOut)
def start_concept_practice(
    concept_slug: str,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> PracticeProgressOut:
    concept = db.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is None:
        raise NotFoundError(f"Unknown concept '{concept_slug}'.")
    domain = concept.domain
    if domain is None:
        raise NotFoundError(f"Concept '{concept_slug}' has no assessment domain.")

    attempt = assessment_service.start_attempt(db, student_profile, domain.slug)
    next_question = assessment_service.select_next_question(db, attempt, concept_slug=concept_slug)
    answered, total = assessment_service.concept_progress(db, student_profile.id, concept_slug)

    is_complete = next_question is None
    if is_complete:
        assessment_service.complete_attempt(db, student_profile, attempt)

    return PracticeProgressOut(
        attempt_id=attempt.id,
        concept_slug=concept_slug,
        next_question=_practice_question_out(next_question),
        is_complete=is_complete,
        answered_in_concept=answered,
        total_in_concept=total,
    )


@router.post("/practice/{concept_slug}/attempts/{attempt_id}/answer", response_model=PracticeProgressOut)
def answer_concept_practice(
    concept_slug: str,
    attempt_id: uuid.UUID,
    payload: PracticeAnswerRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> PracticeProgressOut:
    attempt = assessment_service.get_attempt(db, attempt_id)
    if attempt is None or attempt.student_profile_id != student_profile.id:
        raise NotFoundError("Practice session not found.")
    question = db.get(Question, payload.question_id)
    if question is None:
        raise NotFoundError("Question not found.")

    response = assessment_service.submit_response(
        db, attempt, question, payload.response_payload, payload.time_spent_seconds
    )
    db.refresh(attempt)
    next_question = assessment_service.select_next_question(db, attempt, concept_slug=concept_slug)
    is_complete = next_question is None
    answered, total = assessment_service.concept_progress(db, student_profile.id, concept_slug)

    if is_complete:
        assessment_service.complete_attempt(db, student_profile, attempt)

    return PracticeProgressOut(
        attempt_id=attempt.id,
        concept_slug=concept_slug,
        is_correct=response.is_correct,
        score=float(response.score) if response.score is not None else None,
        explanation=question.explanation,
        next_question=_practice_question_out(next_question),
        is_complete=is_complete,
        answered_in_concept=answered,
        total_in_concept=total,
    )
