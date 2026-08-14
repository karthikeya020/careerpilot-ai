"""Adaptive assessment engine. Labeled throughout (here and in API
responses) as an adaptive *educational* assessment prototype -- no
psychometric validity is claimed (Prompt 2 requirement).

Adaptive selection is real, if intentionally simple: concept depth (root
concepts before their dependents, via the same ConceptDependency table that
backs GraphRAG root-cause analysis) provides a soft ordering, and a running
difficulty target adjusts up after streaks of correct answers and down after
streaks of incorrect ones. MCQ/multiple-selection are scored by exact-match
arithmetic; free-form types are graded by AssessmentAgent (AI evaluator
behind the provider abstraction, keyword-overlap fallback with no live key).
"""

import uuid
from datetime import date as date_cls
from datetime import datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.assessment_agent import AssessmentAgent, AssessmentGradingInput
from app.career_twin.scoring import recompute_twin
from app.models.assessment import (
    AI_GRADED_QUESTION_TYPES,
    ATTEMPT_STATUS_COMPLETED,
    ATTEMPT_STATUS_IN_PROGRESS,
    DETERMINISTIC_QUESTION_TYPES,
    AssessmentAttempt,
    AssessmentDomain,
    Concept,
    ConceptDependency,
    Question,
    QuestionResponse,
)
from app.models.base import utcnow
from app.models.skill import EVIDENCE_TYPE_ASSESSMENT, Skill, SkillEvidence
from app.models.student import StudentProfile

# 1-2 = easy, 3 = medium, 4-5 = hard -- shared with the API layer so the
# frontend never has to hardcode the same thresholds.
DIFFICULTY_BAND_EASY = "easy"
DIFFICULTY_BAND_MEDIUM = "medium"
DIFFICULTY_BAND_HARD = "hard"


def difficulty_band(difficulty: int) -> str:
    if difficulty <= 2:
        return DIFFICULTY_BAND_EASY
    if difficulty == 3:
        return DIFFICULTY_BAND_MEDIUM
    return DIFFICULTY_BAND_HARD

_DIFFICULTY_MIN = 1
_DIFFICULTY_MAX = 5
_STREAK_WINDOW = 2
_EVIDENCE_SATURATION = 3


def get_domain_by_slug(db: Session, slug: str) -> AssessmentDomain | None:
    return db.scalar(select(AssessmentDomain).where(AssessmentDomain.slug == slug))


class DomainSummary:
    """Plain container (not an ORM model) combining a domain with per-student
    recommendation info, so the API layer can build AssessmentDomainOut
    without re-querying."""

    def __init__(self, domain: AssessmentDomain, question_count: int, recommended: bool, matched_skills: list[str]):
        self.domain = domain
        self.question_count = question_count
        self.recommended = recommended
        self.matched_skills = matched_skills


def list_domains_with_recommendations(db: Session, student_profile: StudentProfile) -> list[DomainSummary]:
    """Recommend domains whose concepts map to a skill the student actually
    has evidence for (resume, onboarding, prior assessments, interviews --
    any SkillEvidence source), so a student never has to guess which of the
    growing question bank is actually relevant to them."""
    domains = list(db.scalars(select(AssessmentDomain)).all())
    student_skill_ids = set(
        db.scalars(select(SkillEvidence.skill_id).where(SkillEvidence.student_profile_id == student_profile.id)).all()
    )

    summaries: list[DomainSummary] = []
    for domain in domains:
        question_count = db.scalar(
            select(func.count()).select_from(Question).where(Question.domain_id == domain.id)
        ) or 0
        concept_skill_ids = set(
            db.scalars(
                select(Concept.skill_id).where(Concept.domain_id == domain.id, Concept.skill_id.isnot(None))
            ).all()
        )
        matched_ids = concept_skill_ids & student_skill_ids
        matched_names = (
            sorted(s.name for s in db.scalars(select(Skill).where(Skill.id.in_(matched_ids))).all())
            if matched_ids
            else []
        )
        summaries.append(
            DomainSummary(domain=domain, question_count=question_count, recommended=bool(matched_ids), matched_skills=matched_names)
        )

    summaries.sort(key=lambda s: (not s.recommended, -len(s.matched_skills), s.domain.name))
    return summaries


def _concept_depth(db: Session, concept_id: uuid.UUID) -> int:
    depth = 0
    frontier = [concept_id]
    seen = {concept_id}
    for _ in range(10):
        deps = db.scalars(select(ConceptDependency).where(ConceptDependency.concept_id.in_(frontier))).all()
        next_frontier = [d.depends_on_id for d in deps if d.depends_on_id not in seen]
        if not next_frontier:
            break
        seen.update(next_frontier)
        frontier = next_frontier
        depth += 1
    return depth


def start_attempt(
    db: Session, student_profile: StudentProfile, domain_slug: str, target_role_id: uuid.UUID | None = None
) -> AssessmentAttempt:
    domain = get_domain_by_slug(db, domain_slug)
    if domain is None:
        raise ValueError(f"Unknown assessment domain '{domain_slug}'")

    attempt = AssessmentAttempt(
        student_profile_id=student_profile.id,
        domain_id=domain.id,
        target_role_id=target_role_id,
        status=ATTEMPT_STATUS_IN_PROGRESS,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def _target_difficulty(responses: list[QuestionResponse]) -> int:
    if not responses:
        return 2
    recent = responses[-_STREAK_WINDOW:]
    if len(recent) == _STREAK_WINDOW and all(r.is_correct for r in recent):
        base = recent[-1].question.difficulty + 1
    elif len(recent) == _STREAK_WINDOW and all(r.is_correct is False for r in recent):
        base = recent[-1].question.difficulty - 1
    else:
        base = recent[-1].question.difficulty
    return max(_DIFFICULTY_MIN, min(_DIFFICULTY_MAX, base))


def _student_answered_question_ids(db: Session, student_profile_id: uuid.UUID, domain_id: uuid.UUID) -> set[uuid.UUID]:
    """Every question this student has EVER answered in this domain, across
    every past attempt -- not just the current one. Without this, a fresh
    attempt in a small domain would immediately start repeating the same
    questions the student already solved last time."""
    return set(
        db.scalars(
            select(QuestionResponse.question_id)
            .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
            .where(
                AssessmentAttempt.student_profile_id == student_profile_id,
                AssessmentAttempt.domain_id == domain_id,
            )
        ).all()
    )


def domain_progress(db: Session, attempt: AssessmentAttempt) -> tuple[int, int]:
    """(questions_answered_ever, total_questions) for this student in this attempt's domain."""
    answered = len(_student_answered_question_ids(db, attempt.student_profile_id, attempt.domain_id))
    total = db.scalar(select(func.count()).select_from(Question).where(Question.domain_id == attempt.domain_id)) or 0
    return answered, total


def concept_progress(db: Session, student_profile_id: uuid.UUID, concept_slug: str) -> tuple[int, int]:
    """(questions_answered_ever, total_questions) for this student, scoped to
    ONE concept -- powers the GraphRAG embedded-practice widget's progress
    indicator and its practice_available flag."""
    concept = db.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is None:
        return 0, 0
    total = db.scalar(select(func.count()).select_from(Question).where(Question.concept_id == concept.id)) or 0
    answered = db.scalar(
        select(func.count(func.distinct(QuestionResponse.question_id)))
        .select_from(QuestionResponse)
        .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
        .where(
            AssessmentAttempt.student_profile_id == student_profile_id,
            QuestionResponse.concept_id == concept.id,
        )
    ) or 0
    return answered, total


def select_next_question(db: Session, attempt: AssessmentAttempt, concept_slug: str | None = None) -> Question | None:
    answered_ids = _student_answered_question_ids(db, attempt.student_profile_id, attempt.domain_id)
    query = select(Question).where(Question.domain_id == attempt.domain_id, Question.id.notin_(answered_ids))
    if concept_slug is not None:
        concept = db.scalar(select(Concept).where(Concept.slug == concept_slug, Concept.domain_id == attempt.domain_id))
        if concept is None:
            return None
        query = query.where(Question.concept_id == concept.id)
    candidates = db.scalars(query).all()
    if not candidates:
        return None

    target_difficulty = _target_difficulty(list(attempt.responses))
    depth_cache: dict[uuid.UUID, int] = {}

    def sort_key(question: Question) -> tuple:
        depth = depth_cache.setdefault(question.concept_id, _concept_depth(db, question.concept_id))
        return (depth, abs(question.difficulty - target_difficulty))

    candidates_sorted = sorted(candidates, key=sort_key)
    return candidates_sorted[0]


def submit_response(
    db: Session,
    attempt: AssessmentAttempt,
    question: Question,
    response_payload: dict,
    time_spent_seconds: int | None = None,
) -> QuestionResponse:
    if question.question_type in DETERMINISTIC_QUESTION_TYPES:
        selected = set(response_payload.get("selected_option_ids", []))
        correct = set(question.correct_answer.get("correct_option_ids", []))
        is_correct = selected == correct
        score = 1.0 if is_correct else round(len(selected & correct) / max(len(correct), 1) * 0.5, 4)
        ai_evaluated = False
        evaluator_confidence = None
    elif question.question_type in AI_GRADED_QUESTION_TYPES:
        agent = AssessmentAgent()
        output, _latency = agent.safe_run(
            AssessmentGradingInput(
                question_prompt=question.prompt,
                response_text=response_payload.get("response_text", ""),
                keywords=question.correct_answer.get("keywords", []),
                sample_answer=question.correct_answer.get("sample_answer", ""),
            )
        )
        score = output.score
        is_correct = output.is_correct
        ai_evaluated = True
        evaluator_confidence = output.confidence
    else:
        raise ValueError(f"Unknown question type '{question.question_type}'")

    response = QuestionResponse(
        attempt_id=attempt.id,
        question_id=question.id,
        concept_id=question.concept_id,
        response_payload=response_payload,
        is_correct=is_correct,
        score=score,
        ai_evaluated=ai_evaluated,
        evaluator_confidence=evaluator_confidence,
        time_spent_seconds=time_spent_seconds,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


def complete_attempt(db: Session, student_profile: StudentProfile, attempt: AssessmentAttempt) -> AssessmentAttempt:
    responses = list(attempt.responses)
    scored = [float(r.score) for r in responses if r.score is not None]
    if scored:
        attempt.score = round(sum(scored) / len(scored), 4)
        attempt.confidence = round(min(len(scored) / _EVIDENCE_SATURATION, 1.0) * 0.7, 4)
    else:
        attempt.score = None
        attempt.confidence = None
    attempt.status = ATTEMPT_STATUS_COMPLETED
    attempt.completed_at = utcnow()
    db.commit()
    db.refresh(attempt)

    record_assessment_evidence(db, student_profile, attempt)
    recompute_twin(db, student_profile, reason=f"Completed '{attempt.domain.name}' assessment attempt.")
    return attempt


def record_assessment_evidence(db: Session, student_profile: StudentProfile, attempt: AssessmentAttempt) -> list[SkillEvidence]:
    created: list[SkillEvidence] = []
    for response in attempt.responses:
        concept = db.get(Concept, response.concept_id)
        if concept is None or concept.skill_id is None:
            continue
        evidence = SkillEvidence(
            student_profile_id=student_profile.id,
            skill_id=concept.skill_id,
            concept_id=concept.id,
            evidence_type=EVIDENCE_TYPE_ASSESSMENT,
            source_object_type="question_response",
            source_object_id=response.id,
            raw_score=float(response.score or 0.0),
            normalized_score=float(response.score or 0.0),
            weight=1.0 if not response.ai_evaluated else 0.85,
            confidence=float(response.evaluator_confidence) if response.evaluator_confidence is not None else 0.75,
            explanation=(
                f"{'Correct' if response.is_correct else 'Incorrect'} answer to a {attempt.domain.name} question "
                f"testing '{concept.name}'."
            ),
        )
        db.add(evidence)
        created.append(evidence)
    if created:
        db.commit()
        for e in created:
            db.refresh(e)
    return created


def get_attempt(db: Session, attempt_id: uuid.UUID) -> AssessmentAttempt | None:
    return db.get(AssessmentAttempt, attempt_id)


# ============================================================================
# Activity calendar & analytics -- entirely derived from QuestionResponse rows
# that already exist for scoring (Constitution rule 1: no invented numbers).
# No new tables: every count here is a real read of stored responses.
# ============================================================================

def _student_responses(student_profile_id: uuid.UUID):
    return (
        select(QuestionResponse, Question, AssessmentDomain)
        .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
        .join(Question, QuestionResponse.question_id == Question.id)
        .join(AssessmentDomain, Question.domain_id == AssessmentDomain.id)
        .where(AssessmentAttempt.student_profile_id == student_profile_id)
    )


def get_activity_calendar(db: Session, student_profile: StudentProfile, year: int) -> list[dict]:
    """One entry per day that has at least one response in `year`:
    {"date": "YYYY-MM-DD", "count": int, "correct_count": int}. Days with zero
    activity are simply absent -- the frontend fills the grid around this."""
    rows = db.execute(
        select(QuestionResponse.created_at, QuestionResponse.is_correct)
        .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
        .where(
            AssessmentAttempt.student_profile_id == student_profile.id,
            QuestionResponse.created_at >= datetime(year, 1, 1),
            QuestionResponse.created_at < datetime(year + 1, 1, 1),
        )
    ).all()

    daily: dict[str, dict] = {}
    for created_at, is_correct in rows:
        key = created_at.date().isoformat()
        bucket = daily.setdefault(key, {"date": key, "count": 0, "correct_count": 0})
        bucket["count"] += 1
        if is_correct:
            bucket["correct_count"] += 1
    return sorted(daily.values(), key=lambda d: d["date"])


def get_activity_for_date(db: Session, student_profile: StudentProfile, day: date_cls) -> list[dict]:
    """Every question the student answered on `day`, in submission order --
    powers the calendar's click-to-drill-down detail panel."""
    start = datetime.combine(day, time.min)
    end = start + timedelta(days=1)
    rows = db.execute(
        _student_responses(student_profile.id)
        .where(QuestionResponse.created_at >= start, QuestionResponse.created_at < end)
        .order_by(QuestionResponse.created_at)
    ).all()
    return [
        {
            "response_id": response.id,
            "question_id": question.id,
            "prompt": question.prompt,
            "domain_name": domain.name,
            "concept_name": question.concept.name,
            "difficulty": question.difficulty,
            "difficulty_band": difficulty_band(question.difficulty),
            "question_type": question.question_type,
            "is_correct": response.is_correct,
            "score": float(response.score) if response.score is not None else None,
            "submitted_at": response.created_at,
        }
        for response, question, domain in rows
    ]


def _compute_streaks(active_days: set[date_cls]) -> tuple[int, int]:
    if not active_days:
        return 0, 0
    ordered = sorted(active_days)
    longest = current_run = 1
    for previous, current in zip(ordered, ordered[1:]):
        if (current - previous).days == 1:
            current_run += 1
            longest = max(longest, current_run)
        else:
            current_run = 1

    today = utcnow().date()
    if today in active_days:
        cursor = today
    elif (today - timedelta(days=1)) in active_days:
        # yesterday still "counts" today so a streak doesn't visually reset to
        # 0 the instant midnight passes before the student has practiced yet.
        cursor = today - timedelta(days=1)
    else:
        return 0, longest

    current_streak = 0
    while cursor in active_days:
        current_streak += 1
        cursor -= timedelta(days=1)
    return current_streak, longest


def get_analytics(db: Session, student_profile: StudentProfile) -> dict:
    rows = db.execute(_student_responses(student_profile.id)).all()

    total = len(rows)
    correct = sum(1 for response, _q, _d in rows if response.is_correct)

    domain_stats: dict[str, dict] = {}
    band_stats: dict[str, dict] = {}
    daily_scores: dict[str, list[float]] = {}
    active_days: set[date_cls] = set()

    for response, question, domain in rows:
        d_bucket = domain_stats.setdefault(domain.name, {"domain": domain.name, "answered": 0, "correct": 0})
        d_bucket["answered"] += 1
        if response.is_correct:
            d_bucket["correct"] += 1

        band = difficulty_band(question.difficulty)
        b_bucket = band_stats.setdefault(band, {"band": band, "answered": 0, "correct": 0})
        b_bucket["answered"] += 1
        if response.is_correct:
            b_bucket["correct"] += 1

        active_days.add(response.created_at.date())
        if response.score is not None:
            daily_scores.setdefault(response.created_at.date().isoformat(), []).append(float(response.score))

    accuracy_by_domain = [
        {"domain": v["domain"], "accuracy": round(v["correct"] / v["answered"], 4), "answered": v["answered"]}
        for v in sorted(domain_stats.values(), key=lambda v: v["domain"])
    ]
    band_order = {DIFFICULTY_BAND_EASY: 0, DIFFICULTY_BAND_MEDIUM: 1, DIFFICULTY_BAND_HARD: 2}
    accuracy_by_difficulty = [
        {"band": v["band"], "accuracy": round(v["correct"] / v["answered"], 4), "answered": v["answered"]}
        for v in sorted(band_stats.values(), key=lambda v: band_order.get(v["band"], 99))
    ]
    score_trend = [
        {"date": day, "avg_score": round(sum(scores) / len(scores), 4)}
        for day, scores in sorted(daily_scores.items())
    ]
    current_streak, longest_streak = _compute_streaks(active_days)

    return {
        "total_answered": total,
        "total_correct": correct,
        "overall_accuracy": round(correct / total, 4) if total else None,
        "accuracy_by_domain": accuracy_by_domain,
        "accuracy_by_difficulty": accuracy_by_difficulty,
        "score_trend": score_trend,
        "current_streak_days": current_streak,
        "longest_streak_days": longest_streak,
        "active_day_count": len(active_days),
    }
