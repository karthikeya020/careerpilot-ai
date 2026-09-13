"""LeetCode problem completions + the "explain how you solved" code review.

This is now the only progress the Assessment page tracks: quiz responses
feed weakness detection only (leetcode_recommendation_service), and the
practice-activity view is built from these rows.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.code_review_agent import CodeReviewAgent, CodeReviewInput
from app.core.errors import NotFoundError
from app.data.leetcode_catalog import (
    CONCEPT_APPROACH,
    concept_for_slug,
    problem_url,
    similar_problems,
)
from app.models.base import utcnow
from app.models.leetcode import LeetCodeCompletion
from app.models.student import StudentProfile
from app.schemas.leetcode_completion import (
    AnalyzeCodeRequest,
    CodeReviewOut,
    LeetCodeAnalysisOut,
    LeetCodeCompletionOut,
    MarkCompleteRequest,
    SimilarProblemOut,
)

_GENERIC_APPROACH = (
    "Write the brute force first and name its time cost. Then look for repeated work you can cache "
    "(a hash map), structure you can exploit (sorted input -> two pointers / binary search), or state "
    "you can carry in one pass (a running total or window). Re-check the space cost at the end."
)


def _to_out(row: LeetCodeCompletion) -> LeetCodeCompletionOut:
    return LeetCodeCompletionOut(
        slug=row.problem_slug,
        title=row.problem_title,
        difficulty=row.difficulty,
        concept_slug=row.concept_slug,
        domain_slug=row.domain_slug,
        completed_at=row.completed_at.isoformat(),
        analyzed_at=row.analyzed_at.isoformat() if row.analyzed_at else None,
        has_analysis=row.analysis is not None,
    )


def _get_row(db: Session, student_profile_id, slug: str) -> LeetCodeCompletion | None:
    return db.scalar(
        select(LeetCodeCompletion).where(
            LeetCodeCompletion.student_profile_id == student_profile_id,
            LeetCodeCompletion.problem_slug == slug,
        )
    )


def list_completions(db: Session, student_profile: StudentProfile) -> list[LeetCodeCompletionOut]:
    rows = db.scalars(
        select(LeetCodeCompletion)
        .where(LeetCodeCompletion.student_profile_id == student_profile.id)
        .order_by(LeetCodeCompletion.completed_at.desc())
    ).all()
    return [_to_out(r) for r in rows]


def mark_complete(
    db: Session, student_profile: StudentProfile, payload: MarkCompleteRequest
) -> LeetCodeCompletionOut:
    row = _get_row(db, student_profile.id, payload.slug)
    if row is None:
        row = LeetCodeCompletion(
            student_profile_id=student_profile.id,
            problem_slug=payload.slug,
            problem_title=payload.title,
            difficulty=payload.difficulty or "",
            concept_slug=payload.concept_slug or concept_for_slug(payload.slug),
            domain_slug=payload.domain_slug,
            completed_at=utcnow(),
        )
        db.add(row)
    else:
        # Re-marking refreshes the timestamp and any newly-known metadata.
        row.completed_at = utcnow()
        row.problem_title = payload.title or row.problem_title
        row.difficulty = payload.difficulty or row.difficulty
        row.concept_slug = payload.concept_slug or row.concept_slug or concept_for_slug(payload.slug)
        row.domain_slug = payload.domain_slug or row.domain_slug
    db.commit()
    db.refresh(row)
    return _to_out(row)


def unmark(db: Session, student_profile: StudentProfile, slug: str) -> None:
    row = _get_row(db, student_profile.id, slug)
    if row is not None:
        db.delete(row)
        db.commit()


def _how_to_think(concept_slug: str | None, slug: str) -> str:
    concept = concept_slug or concept_for_slug(slug)
    return CONCEPT_APPROACH.get(concept or "", _GENERIC_APPROACH)


def _similar(slug: str, concept_slug: str | None, domain_slug: str | None) -> list[SimilarProblemOut]:
    return [
        SimilarProblemOut(slug=s, title=t, difficulty=d, url=problem_url(s))
        for s, t, d in similar_problems(slug, concept_slug, domain_slug)
    ]


def get_analysis(db: Session, student_profile: StudentProfile, slug: str) -> LeetCodeAnalysisOut:
    row = _get_row(db, student_profile.id, slug)
    if row is None:
        raise NotFoundError("Mark the problem complete before opening its analysis.")
    review = CodeReviewOut(**row.analysis) if row.analysis else None
    return LeetCodeAnalysisOut(
        slug=row.problem_slug,
        title=row.problem_title,
        how_to_think=_how_to_think(row.concept_slug, slug),
        similar_problems=_similar(slug, row.concept_slug, row.domain_slug),
        language=row.language,
        code=row.code,
        review=review,
        analyzed_at=row.analyzed_at.isoformat() if row.analyzed_at else None,
    )


def analyze_code(
    db: Session, student_profile: StudentProfile, slug: str, payload: AnalyzeCodeRequest
) -> LeetCodeAnalysisOut:
    row = _get_row(db, student_profile.id, slug)
    if row is None:
        raise NotFoundError("Mark the problem complete before submitting a solution.")

    how = _how_to_think(row.concept_slug, slug)
    agent = CodeReviewAgent()
    output, _latency = agent.safe_run(
        CodeReviewInput(
            question_title=row.problem_title,
            concept_slug=row.concept_slug or "",
            how_to_think=how,
            language=payload.language or "",
            code=payload.code,
        )
    )
    review = CodeReviewOut(
        summary=output.summary,
        strengths=output.strengths,
        improvements=output.improvements,
        time_complexity=output.time_complexity,
        space_complexity=output.space_complexity,
        complexity_explanation=output.complexity_explanation,
        how_to_think=output.how_to_think or how,
        ai_generated=output.ai_generated,
    )

    row.code = payload.code
    row.language = payload.language
    row.analysis = review.model_dump()
    row.analyzed_at = utcnow()
    db.commit()
    db.refresh(row)

    return LeetCodeAnalysisOut(
        slug=row.problem_slug,
        title=row.problem_title,
        how_to_think=how,
        similar_problems=_similar(slug, row.concept_slug, row.domain_slug),
        language=row.language,
        code=row.code,
        review=review,
        analyzed_at=row.analyzed_at.isoformat(),
    )
