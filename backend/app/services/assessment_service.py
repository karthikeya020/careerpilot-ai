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

from sqlalchemy import select
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
from app.models.skill import EVIDENCE_TYPE_ASSESSMENT, SkillEvidence
from app.models.student import StudentProfile

_DIFFICULTY_MIN = 1
_DIFFICULTY_MAX = 5
_STREAK_WINDOW = 2
_EVIDENCE_SATURATION = 3


def get_domain_by_slug(db: Session, slug: str) -> AssessmentDomain | None:
    return db.scalar(select(AssessmentDomain).where(AssessmentDomain.slug == slug))


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


def select_next_question(db: Session, attempt: AssessmentAttempt) -> Question | None:
    answered_ids = {r.question_id for r in attempt.responses}
    candidates = db.scalars(
        select(Question).where(Question.domain_id == attempt.domain_id, Question.id.notin_(answered_ids))
    ).all()
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
