"""Recommend LeetCode problems for the concepts a student is weakest on.

Weakness is measured, not guessed: it comes straight from the student's own
stored `QuestionResponse` rows (per-concept accuracy), the same data the
analytics panel and Career Twin already use (Constitution rule 1: no
invented numbers). Problem picks come from the curated static
app/data/leetcode_catalog.py -- nothing is fetched at request time.

Selection:
  1. Group the student's responses by concept, compute accuracy.
  2. A concept is "weak" if it has >= MIN_ANSWERED responses and accuracy
     below WEAKNESS_THRESHOLD. Weakest first.
  3. Map each weak concept to its catalog problems (falling back to the
     domain list), easiest-first, capped.
  4. If there are no responses at all -> profile fallback: the student's
     resume-matched assessment domains (or all domains), domain-level lists.
  5. If there are responses but no weak concepts -> offer a few "stretch"
     problems from the lowest-accuracy concept, labelled source="no_weaknesses".
"""

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.data.leetcode_catalog import (
    CONCEPT_FOCUS,
    CONCEPT_PROBLEMS,
    DOMAIN_PROBLEMS,
    problem_url,
)
from app.models.assessment import (
    AssessmentAttempt,
    AssessmentDomain,
    Concept,
    Question,
    QuestionResponse,
)
from app.models.student import StudentProfile
from app.schemas.leetcode_recommendation import (
    LeetCodeRecommendationsOut,
    LeetCodeRecommendedProblemOut,
    WeaknessGroupOut,
)
from app.services import assessment_service

WEAKNESS_THRESHOLD = 0.6
MIN_ANSWERED = 2
MAX_GROUPS = 6
MAX_PROBLEMS_PER_GROUP = 5
_DIFFICULTY_ORDER = {"Easy": 0, "Medium": 1, "Hard": 2}


def _problems_for(concept_slug: str | None, domain_slug: str) -> list[LeetCodeRecommendedProblemOut]:
    rows = (concept_slug and CONCEPT_PROBLEMS.get(concept_slug)) or DOMAIN_PROBLEMS.get(domain_slug) or []
    ordered = sorted(rows, key=lambda r: _DIFFICULTY_ORDER.get(r[2], 1))
    seen: set[str] = set()
    out: list[LeetCodeRecommendedProblemOut] = []
    for slug, title, difficulty in ordered:
        if slug in seen:
            continue
        seen.add(slug)
        out.append(
            LeetCodeRecommendedProblemOut(slug=slug, title=title, difficulty=difficulty, url=problem_url(slug))
        )
        if len(out) >= MAX_PROBLEMS_PER_GROUP:
            break
    return out


def _concept_accuracy_rows(db: Session, student_profile_id) -> list[tuple[Concept, AssessmentDomain, int, int]]:
    """(concept, domain, answered, correct) for every concept this student has
    ever answered a question on."""
    correct_expr = func.sum(case((QuestionResponse.is_correct.is_(True), 1), else_=0))
    rows = db.execute(
        select(Concept, AssessmentDomain, func.count(QuestionResponse.id), correct_expr)
        .select_from(QuestionResponse)
        .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
        .join(Concept, QuestionResponse.concept_id == Concept.id)
        .join(AssessmentDomain, Concept.domain_id == AssessmentDomain.id)
        .where(AssessmentAttempt.student_profile_id == student_profile_id)
        .group_by(Concept.id, AssessmentDomain.id)
    ).all()
    return [(c, d, int(answered or 0), int(correct or 0)) for c, d, answered, correct in rows]


def recommend(db: Session, student_profile: StudentProfile) -> LeetCodeRecommendationsOut:
    stats = _concept_accuracy_rows(db, student_profile.id)

    if not stats:
        return _profile_fallback(db, student_profile)

    scored = [
        (concept, domain, answered, correct, correct / answered)
        for concept, domain, answered, correct in stats
        if answered > 0
    ]
    weak = [row for row in scored if row[2] >= MIN_ANSWERED and row[4] < WEAKNESS_THRESHOLD]
    weak.sort(key=lambda row: (row[4], -row[2]))

    if not weak:
        return _no_weakness_stretch(scored)

    groups: list[WeaknessGroupOut] = []
    for concept, domain, answered, _correct, accuracy in weak[:MAX_GROUPS]:
        problems = _problems_for(concept.slug, domain.slug)
        if not problems:
            continue
        groups.append(
            WeaknessGroupOut(
                concept_slug=concept.slug,
                concept_name=concept.name,
                domain_slug=domain.slug,
                domain_name=domain.name,
                accuracy=round(accuracy, 4),
                answered=answered,
                focus=CONCEPT_FOCUS.get(concept.slug, ""),
                problems=problems,
            )
        )

    if not groups:
        return _no_weakness_stretch(scored)

    return LeetCodeRecommendationsOut(
        source="assessment",
        summary=(
            f"{len(groups)} area{'s' if len(groups) != 1 else ''} below "
            f"{int(WEAKNESS_THRESHOLD * 100)}% accuracy in your assessments. "
            "Practising the mapped problems targets each gap directly."
        ),
        weakness_threshold=WEAKNESS_THRESHOLD,
        groups=groups,
    )


def _no_weakness_stretch(scored: list[tuple]) -> LeetCodeRecommendationsOut:
    scored_sorted = sorted(scored, key=lambda row: (row[4], -row[2]))
    groups: list[WeaknessGroupOut] = []
    for concept, domain, answered, _correct, accuracy in scored_sorted[:2]:
        problems = _problems_for(concept.slug, domain.slug)
        if not problems:
            continue
        groups.append(
            WeaknessGroupOut(
                concept_slug=concept.slug,
                concept_name=concept.name,
                domain_slug=domain.slug,
                domain_name=domain.name,
                accuracy=round(accuracy, 4),
                answered=answered,
                focus=CONCEPT_FOCUS.get(concept.slug, ""),
                problems=problems,
            )
        )
    return LeetCodeRecommendationsOut(
        source="no_weaknesses",
        summary=(
            "No assessment area is below the weakness threshold -- nice work. "
            "Here are stretch problems from your lowest-scoring topics to keep pushing."
        ),
        weakness_threshold=WEAKNESS_THRESHOLD,
        groups=groups,
    )


def _profile_fallback(db: Session, student_profile: StudentProfile) -> LeetCodeRecommendationsOut:
    summaries = assessment_service.list_domains_with_recommendations(db, student_profile)
    recommended = [s for s in summaries if s.recommended] or summaries
    groups: list[WeaknessGroupOut] = []
    for summary in recommended[:MAX_GROUPS]:
        domain = summary.domain
        problems = _problems_for(None, domain.slug)
        if not problems:
            continue
        groups.append(
            WeaknessGroupOut(
                concept_slug=None,
                concept_name=domain.name,
                domain_slug=domain.slug,
                domain_name=domain.name,
                accuracy=None,
                answered=0,
                focus=domain.description,
                problems=problems,
            )
        )
    return LeetCodeRecommendationsOut(
        source="profile",
        summary=(
            "No assessment history yet, so these are starter problems for the domains "
            "that match your profile. Take an assessment to get weakness-targeted picks."
        ),
        weakness_threshold=WEAKNESS_THRESHOLD,
        groups=groups,
    )
