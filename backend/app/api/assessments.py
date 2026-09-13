import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.assessment import Question
from app.models.student import StudentProfile
from app.schemas.assessment import (
    ActivityDayDetailOut,
    ActivityDayOut,
    AssessmentAnalyticsOut,
    AssessmentAttemptOut,
    AssessmentDomainOut,
    AttemptProgressOut,
    QuestionOut,
    QuestionResponseOut,
    StartAttemptRequest,
    SubmitResponseRequest,
)
from app.schemas.daily_goal import DailyGoalOut, SetDailyGoalRequest
from app.schemas.leetcode_completion import (
    AnalyzeCodeRequest,
    LeetCodeAnalysisOut,
    LeetCodeCompletionOut,
    MarkCompleteRequest,
)
from app.schemas.leetcode_recommendation import LeetCodeRecommendationsOut
from app.services import (
    assessment_service,
    daily_goal_service,
    leetcode_completion_service,
    leetcode_recommendation_service,
)

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
        difficulty_band=assessment_service.difficulty_band(question.difficulty),
        concept_name=question.concept.name,
    )


@router.get("/domains", response_model=list[AssessmentDomainOut])
def list_domains(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[AssessmentDomainOut]:
    summaries = assessment_service.list_domains_with_recommendations(db, student_profile)
    return [
        AssessmentDomainOut(
            id=s.domain.id,
            slug=s.domain.slug,
            name=s.domain.name,
            description=s.domain.description,
            question_count=s.question_count,
            recommended=s.recommended,
            matched_skills=s.matched_skills,
        )
        for s in summaries
    ]


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
    answered, total = assessment_service.domain_progress(db, attempt)
    return AttemptProgressOut(
        attempt_id=attempt.id,
        response=None,
        next_question=_question_out(next_question),
        is_complete=next_question is None,
        domain_exhausted=next_question is None and answered >= total,
        answered_in_domain=answered,
        total_in_domain=total,
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
    answered, total = assessment_service.domain_progress(db, attempt)

    if is_complete:
        assessment_service.complete_attempt(db, student_profile, attempt)

    response_out = QuestionResponseOut.model_validate(response)
    response_out.explanation = question.explanation

    return AttemptProgressOut(
        attempt_id=attempt.id,
        response=response_out,
        next_question=_question_out(next_question),
        is_complete=is_complete,
        domain_exhausted=is_complete and answered >= total,
        answered_in_domain=answered,
        total_in_domain=total,
    )


@router.get("/activity-calendar", response_model=list[ActivityDayOut])
def get_activity_calendar(
    year: int = Query(..., ge=2000, le=2100),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ActivityDayOut]:
    days = assessment_service.get_activity_calendar(db, student_profile, year)
    return [ActivityDayOut(**d) for d in days]


@router.get("/activity-calendar/{day}", response_model=list[ActivityDayDetailOut])
def get_activity_calendar_day(
    day: date,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ActivityDayDetailOut]:
    entries = assessment_service.get_activity_for_date(db, student_profile, day)
    return [ActivityDayDetailOut(**e) for e in entries]


@router.get("/analytics", response_model=AssessmentAnalyticsOut)
def get_analytics(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> AssessmentAnalyticsOut:
    return AssessmentAnalyticsOut(**assessment_service.get_analytics(db, student_profile))


@router.get("/leetcode-recommendations", response_model=LeetCodeRecommendationsOut)
def get_leetcode_recommendations(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LeetCodeRecommendationsOut:
    return leetcode_recommendation_service.recommend(db, student_profile)


@router.get("/daily-goal", response_model=DailyGoalOut)
def get_daily_goal(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> DailyGoalOut:
    return daily_goal_service.get_daily_goal(db, student_profile)


@router.put("/daily-goal", response_model=DailyGoalOut)
def set_daily_goal(
    payload: SetDailyGoalRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> DailyGoalOut:
    return daily_goal_service.set_goal(db, student_profile, payload.goal)


@router.get("/leetcode-completions", response_model=list[LeetCodeCompletionOut])
def list_leetcode_completions(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[LeetCodeCompletionOut]:
    return leetcode_completion_service.list_completions(db, student_profile)


@router.post("/leetcode-completions", response_model=LeetCodeCompletionOut)
def mark_leetcode_complete(
    payload: MarkCompleteRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LeetCodeCompletionOut:
    return leetcode_completion_service.mark_complete(db, student_profile, payload)


@router.delete("/leetcode-completions/{slug}", status_code=204)
def unmark_leetcode_complete(
    slug: str,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> None:
    leetcode_completion_service.unmark(db, student_profile, slug)


@router.get("/leetcode-completions/{slug}/analysis", response_model=LeetCodeAnalysisOut)
def get_leetcode_analysis(
    slug: str,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LeetCodeAnalysisOut:
    return leetcode_completion_service.get_analysis(db, student_profile, slug)


@router.post("/leetcode-completions/{slug}/analyze", response_model=LeetCodeAnalysisOut)
def analyze_leetcode_solution(
    slug: str,
    payload: AnalyzeCodeRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LeetCodeAnalysisOut:
    return leetcode_completion_service.analyze_code(db, student_profile, slug, payload)
