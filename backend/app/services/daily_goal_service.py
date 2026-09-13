"""Assessment "daily goal": the student types a free-text placement goal
(e.g. "I want to be placed in Microsoft") and gets a fixed set of
DAILY_GOAL_TARGET questions per calendar day, drawn from the assessment
domains that goal maps to.

The mapping is deterministic and inspectable, not an LLM call:
  1. any seeded company name that appears in the goal contributes that
     company's `emphasis_domains` (already assessment-domain slugs);
  2. role/skill keywords ("frontend", "data analyst", "backend", language
     names, ...) contribute their domains;
  3. every placement goal also gets `dsa` (interview staple);
  4. nothing matched -> all domains.

The per-day pick is seeded by (student_id, goal, date) so it's stable
within a day and rotates at midnight. Questions the student hasn't answered
before, from distinct concepts, are preferred. A daily item is "done" once
the student has answered any question in that item's concept today.
"""

import random
from datetime import datetime, time, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import (
    AssessmentAttempt,
    AssessmentDomain,
    Concept,
    Question,
    QuestionResponse,
)
from app.models.audit import AuditEvent
from app.models.base import utcnow
from app.models.job_catalog import CompanyJobListing
from app.models.student import StudentProfile
from app.schemas.daily_goal import DAILY_GOAL_TARGET, DailyGoalOut, DailyGoalQuestionOut
from app.services import assessment_service

_ALL_DOMAIN_SLUGS = ("dsa", "oop", "java", "python", "javascript", "sql")

# keyword (substring, lower-cased) -> domain slugs it implies
_KEYWORD_DOMAINS: list[tuple[str, tuple[str, ...]]] = [
    ("front end", ("javascript", "oop")),
    ("frontend", ("javascript", "oop")),
    ("front-end", ("javascript", "oop")),
    ("react", ("javascript",)),
    ("ui engineer", ("javascript",)),
    ("web develop", ("javascript", "oop")),
    ("back end", ("java", "sql", "oop")),
    ("backend", ("java", "sql", "oop")),
    ("back-end", ("java", "sql", "oop")),
    ("api ", ("java", "sql")),
    ("micro service", ("java", "oop", "sql")),
    ("microservice", ("java", "oop", "sql")),
    ("full stack", ("javascript", "java", "sql")),
    ("fullstack", ("javascript", "java", "sql")),
    ("full-stack", ("javascript", "java", "sql")),
    ("data analyst", ("sql", "python")),
    ("data analytics", ("sql", "python")),
    ("data engineer", ("sql", "python", "dsa")),
    ("data scientist", ("python", "sql", "dsa")),
    ("data science", ("python", "sql", "dsa")),
    ("machine learning", ("python", "dsa")),
    ("deep learning", ("python", "dsa")),
    (" ml ", ("python", "dsa")),
    (" ai ", ("python", "dsa")),
    ("analyst", ("sql", "python")),
    ("business intelligence", ("sql",)),
    ("sde", ("dsa", "oop", "java")),
    (" swe", ("dsa", "oop", "java")),
    ("software engineer", ("dsa", "oop", "java")),
    ("software develop", ("dsa", "oop", "java")),
    ("developer", ("dsa", "oop")),
    ("programmer", ("dsa", "oop")),
    ("devops", ("python", "sql")),
    (" sre", ("python", "sql")),
    ("database", ("sql",)),
    ("android", ("java", "oop")),
    ("python", ("python",)),
    ("javascript", ("javascript",)),
    ("typescript", ("javascript",)),
    (" java", ("java",)),
    (" sql", ("sql",)),
    ("dsa", ("dsa",)),
    ("data structures", ("dsa",)),
    ("algorithm", ("dsa",)),
]


def _goal_to_domain_slugs(db: Session, goal: str) -> list[str]:
    text = f" {goal.lower().strip()} "
    slugs: list[str] = []

    def add(candidates) -> None:
        for slug in candidates:
            if slug in _ALL_DOMAIN_SLUGS and slug not in slugs:
                slugs.append(slug)

    # 1. seeded companies mentioned in the goal
    for company, emphasis in db.execute(
        select(CompanyJobListing.company, CompanyJobListing.emphasis_domains)
    ).all():
        if company and company.lower() in text:
            add(emphasis or [])

    # 2. role / skill keywords
    for needle, domains in _KEYWORD_DOMAINS:
        if needle in text:
            add(domains)

    # 3. every placement goal gets DSA
    add(("dsa",))

    # 4. nothing matched -> everything
    if not slugs:
        add(_ALL_DOMAIN_SLUGS)
    return slugs


def _answered_before_today_question_ids(db: Session, student_profile_id) -> set:
    """Questions answered on an earlier day. Used only to *prefer* unseen
    questions when building the set -- deliberately excludes today's answers
    so the daily set stays stable as the student works through it (today's
    practice flips done_today, never membership)."""
    start = datetime.combine(utcnow().date(), time.min)
    return set(
        db.scalars(
            select(QuestionResponse.question_id)
            .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
            .where(
                AssessmentAttempt.student_profile_id == student_profile_id,
                QuestionResponse.created_at < start,
            )
        ).all()
    )


def _concepts_answered_today(db: Session, student_profile_id) -> set:
    start = datetime.combine(utcnow().date(), time.min)
    return set(
        db.scalars(
            select(QuestionResponse.concept_id)
            .join(AssessmentAttempt, QuestionResponse.attempt_id == AssessmentAttempt.id)
            .where(
                AssessmentAttempt.student_profile_id == student_profile_id,
                QuestionResponse.created_at >= start,
                QuestionResponse.created_at < start + timedelta(days=1),
            )
        ).all()
    )


def _select_daily_questions(
    candidates: list[Question], rng: random.Random, answered_before_today: set
) -> list[Question]:
    shuffled = candidates[:]
    rng.shuffle(shuffled)

    picked: list[Question] = []
    used_concepts: set = set()

    def take(pred) -> None:
        for q in shuffled:
            if len(picked) >= DAILY_GOAL_TARGET:
                return
            if q in picked:
                continue
            if pred(q):
                picked.append(q)
                used_concepts.add(q.concept_id)

    # 1. unseen questions, one per concept
    take(lambda q: q.id not in answered_before_today and q.concept_id not in used_concepts)
    # 2. any unseen question
    take(lambda q: q.id not in answered_before_today)
    # 3. seen questions, new concept
    take(lambda q: q.concept_id not in used_concepts)
    # 4. anything left
    take(lambda q: True)
    return picked[:DAILY_GOAL_TARGET]


def get_daily_goal(db: Session, student_profile: StudentProfile) -> DailyGoalOut:
    today = utcnow().date()
    goal = (student_profile.assessment_goal or "").strip() or None
    if goal is None:
        return DailyGoalOut(goal=None, date=today.isoformat())

    domain_slugs = _goal_to_domain_slugs(db, goal)
    domains = {
        d.slug: d
        for d in db.scalars(select(AssessmentDomain).where(AssessmentDomain.slug.in_(domain_slugs))).all()
    }
    ordered_domains = [domains[s] for s in domain_slugs if s in domains]

    candidates = list(
        db.scalars(
            select(Question)
            .join(Concept, Question.concept_id == Concept.id)
            .where(Question.domain_id.in_([d.id for d in ordered_domains]))
        ).all()
    )

    rng = random.Random(f"{student_profile.id}|{goal}|{today.isoformat()}")
    answered_before_today = _answered_before_today_question_ids(db, student_profile.id)
    chosen = _select_daily_questions(candidates, rng, answered_before_today)

    concepts_done = _concepts_answered_today(db, student_profile.id)
    items: list[DailyGoalQuestionOut] = []
    for q in chosen:
        concept = q.concept
        domain = concept.domain
        items.append(
            DailyGoalQuestionOut(
                question_id=q.id,
                prompt=q.prompt,
                domain_slug=domain.slug,
                domain_name=domain.name,
                concept_slug=concept.slug,
                concept_name=concept.name,
                difficulty=q.difficulty,
                difficulty_band=assessment_service.difficulty_band(q.difficulty),
                done_today=q.concept_id in concepts_done,
            )
        )

    return DailyGoalOut(
        goal=goal,
        date=today.isoformat(),
        matched_domains=[d.name for d in ordered_domains],
        target_per_day=DAILY_GOAL_TARGET,
        completed_today=sum(1 for it in items if it.done_today),
        questions=items,
    )


def set_goal(db: Session, student_profile: StudentProfile, raw_goal: str) -> DailyGoalOut:
    new_goal = (raw_goal or "").strip() or None
    if new_goal != student_profile.assessment_goal:
        student_profile.assessment_goal = new_goal
        db.add(
            AuditEvent(
                student_profile_id=student_profile.id,
                event_type="assessment_goal_set",
                payload={"goal": new_goal or ""},
            )
        )
        db.commit()
        db.refresh(student_profile)
    return get_daily_goal(db, student_profile)
