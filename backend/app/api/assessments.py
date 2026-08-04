import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.assessment import AssessmentDomain, Question
from app.models.student import StudentProfile
from app.schemas.assessment import (
    AssessmentAttemptOut,
    AssessmentDomainOut,
    AttemptProgressOut,
    QuestionOut,
    QuestionResponseOut,
    StartAttemptRequest,
    SubmitResponseRequest,
)
from app.services import assessment_service

router = APIRouter(prefix="/assessments", tags=["assessments"])


def _question_out(question: Question | None) -> QuestionOut | None:
    if question is None:
        return None
    return QuestionOut(
        id=question.id,
        question_type=question.question_type,
        prompt=question.prompt,
        options=question.options,
        difficulty=question.difficulty,
        concept_name=question.concept.name,
    )


@router.get("/domains", response_model=list[AssessmentDomainOut])
def list_domains(db: Session = Depends(get_db)) -> list[AssessmentDomain]:
    return list(db.scalars(select(AssessmentDomain)).all())


@router.post("/attempts", response_model=AttemptProgressOut)
def start_attempt(
    payload: StartAttemptRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> AttemptProgressOut:
    try:
        attempt = assessment_service.start_attempt(db, student_profile, payload.domain_slug, payload.target_role_id)
    except ValueError as exc:
        raise NotFoundError(str(exc)) from exc
    next_question = assessment_service.select_next_question(db, attempt)
    return AttemptProgressOut(
        attempt_id=attempt.id,
        response=None,
        next_question=_question_out(next_question),
        is_complete=next_question is None,
    )


@router.get("/attempts/{attempt_id}", response_model=AssessmentAttemptOut)
def get_attempt(
    attempt_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> AssessmentAttemptOut:
    attempt = assessment_service.get_attempt(db, attempt_id)
    if attempt is None or attempt.student_profile_id != student_profile.id:
        raise NotFoundError("Assessment attempt not found.")
    return AssessmentAttemptOut.model_validate(attempt)


@router.post("/attempts/{attempt_id}/responses", response_model=AttemptProgressOut)
def submit_response(
    attempt_id: uuid.UUID,
    payload: SubmitResponseRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> AttemptProgressOut:
    attempt = assessment_service.get_attempt(db, attempt_id)
    if attempt is None or attempt.student_profile_id != student_profile.id:
        raise NotFoundError("Assessment attempt not found.")
    question = db.get(Question, payload.question_id)
    if question is None:
        raise NotFoundError("Question not found.")

    response = assessment_service.submit_response(
        db, attempt, question, payload.response_payload, payload.time_spent_seconds
    )
    db.refresh(attempt)
    next_question = assessment_service.select_next_question(db, attempt)
    is_complete = next_question is None

    if is_complete:
        assessment_service.complete_attempt(db, student_profile, attempt)

    return AttemptProgressOut(
        attempt_id=attempt.id,
        response=QuestionResponseOut.model_validate(response),
        next_question=_question_out(next_question),
        is_complete=is_complete,
    )
