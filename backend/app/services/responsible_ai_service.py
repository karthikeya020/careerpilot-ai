"""Responsible AI Center: surfaces exactly what the system evaluates, what
it doesn't, model/formula/policy versions, evidence provenance, human-review
status, and implements the self-service data controls (export, audio
deletion, account deletion) Prompt-3-class governance requires. Every value
here is read from already-stored data or fixed version constants -- nothing
is computed fresh for this view.
"""

import uuid
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.agents.assessment_agent import PROMPT_VERSION as ASSESSMENT_PROMPT_VERSION
from app.agents.career_coach_agent import PROMPT_VERSION as CAREER_COACH_PROMPT_VERSION
from app.agents.experiment_explainer_agent import (
    PROMPT_VERSION as EXPERIMENT_EXPLAINER_PROMPT_VERSION,
)
from app.agents.hr_agent import PROMPT_VERSION as HR_PROMPT_VERSION
from app.agents.resume_intelligence_agent import (
    PROMPT_VERSION as RESUME_INTELLIGENCE_PROMPT_VERSION,
)
from app.agents.technical_agent import PROMPT_VERSION as TECHNICAL_PROMPT_VERSION
from app.care_engine.policy import POLICY_VERSION
from app.career_twin.scoring import SCORING_RULE_VERSION
from app.core.config import get_settings
from app.models.assessment import AssessmentAttempt
from app.models.audit import AuditEvent
from app.models.care import CareExecution
from app.models.career_twin import CareerTwinSnapshot
from app.models.experiment import ExperimentScenario
from app.models.interview import InterviewAnswer, InterviewSession
from app.models.job_description import JobDescription
from app.models.mission import LearningMission
from app.models.resume import Resume
from app.models.skill import SkillEvidence
from app.models.student import StudentProfile
from app.models.user import User
from app.simulation.engine import SIMULATION_ENGINE_VERSION

AGENT_PROMPT_VERSIONS = {
    "assessment": ASSESSMENT_PROMPT_VERSION,
    "career_coach": CAREER_COACH_PROMPT_VERSION,
    "hr": HR_PROMPT_VERSION,
    "technical": TECHNICAL_PROMPT_VERSION,
    "resume_intelligence": RESUME_INTELLIGENCE_PROMPT_VERSION,
    "experiment_explainer": EXPERIMENT_EXPLAINER_PROMPT_VERSION,
}

EVALUATES = [
    "Resume and job-description keyword/skill coverage (deterministic arithmetic)",
    "Technical and behavioral assessment answers, against a stored rubric",
    "Interview answer relevance, correctness, depth, structure, and communication metrics",
    "Whether an interview claim is supported by uploaded resume evidence (keyword-grounded, not a lie-detection judgment)",
    "Root-cause concept dependencies behind a missed question (graph traversal)",
    "Deterministic what-if scenario simulations for hour allocations",
]

DOES_NOT_EVALUATE = [
    "Probability of being hired, or any hiring outcome",
    "Honesty, personality, or emotional/mental state",
    "Facial expression, tone-as-emotion, or any biometric signal",
    "Cross-student ranking or comparison",
    "Anything without at least one linked evidence record or an explicit insufficient-evidence status",
]


def get_overview(db: Session, student_profile: StudentProfile) -> dict:
    pending_human_review = db.scalar(
        select(func.count())
        .select_from(CareExecution)
        .where(CareExecution.student_profile_id == student_profile.id, CareExecution.requires_human_review.is_(True))
    ) or 0

    evidence_count_rows = db.execute(
        select(SkillEvidence.evidence_type, func.count())
        .where(SkillEvidence.student_profile_id == student_profile.id)
        .group_by(SkillEvidence.evidence_type)
    ).all()
    evidence_counts: dict[str, int] = {row[0]: row[1] for row in evidence_count_rows}

    audio_answers = db.scalars(select(InterviewAnswer).join(InterviewAnswer.question)).all()
    stored_audio_count = sum(
        1
        for a in audio_answers
        if a.audio_storage_path is not None and a.question.session.student_profile_id == student_profile.id
    )

    latest_snapshot = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )

    return {
        "evaluates": EVALUATES,
        "does_not_evaluate": DOES_NOT_EVALUATE,
        "versions": {
            "care_policy_version": POLICY_VERSION,
            "career_twin_formula_version": SCORING_RULE_VERSION,
            "simulation_engine_version": SIMULATION_ENGINE_VERSION,
            "agent_prompt_versions": AGENT_PROMPT_VERSIONS,
        },
        "human_review": {
            "pending_count": pending_human_review,
        },
        "evidence_provenance": evidence_counts,
        "current_career_twin_confidence": (
            float(latest_snapshot.overall_confidence)
            if latest_snapshot is not None and latest_snapshot.overall_confidence is not None
            else None
        ),
        "consent": student_profile.consent_settings,
        "stored_interview_audio_count": stored_audio_count,
        "non_claims": [
            "No hiring probability is ever computed or displayed.",
            "No automatic hiring or admission decision is made by this system.",
            "No public ranking of students is shown to any role.",
            "No lie-detection or deception inference is performed.",
            "No emotional or psychological state is inferred or presented as fact.",
        ],
    }


def export_student_data(db: Session, student_profile: StudentProfile) -> dict:
    """A full, human-readable JSON export of everything stored about this
    student -- the self-service data-export control."""
    resumes = db.scalars(select(Resume).where(Resume.student_profile_id == student_profile.id)).all()
    job_descriptions = db.scalars(
        select(JobDescription).where(JobDescription.student_profile_id == student_profile.id)
    ).all()
    evidence = db.scalars(select(SkillEvidence).where(SkillEvidence.student_profile_id == student_profile.id)).all()
    snapshots = db.scalars(
        select(CareerTwinSnapshot).where(CareerTwinSnapshot.student_profile_id == student_profile.id)
    ).all()
    missions = db.scalars(
        select(LearningMission).where(LearningMission.student_profile_id == student_profile.id)
    ).all()
    assessments = db.scalars(
        select(AssessmentAttempt).where(AssessmentAttempt.student_profile_id == student_profile.id)
    ).all()
    interviews = db.scalars(
        select(InterviewSession).where(InterviewSession.student_profile_id == student_profile.id)
    ).all()
    scenarios = db.scalars(
        select(ExperimentScenario).where(ExperimentScenario.student_profile_id == student_profile.id)
    ).all()
    audit_events = db.scalars(
        select(AuditEvent).where(AuditEvent.student_profile_id == student_profile.id)
    ).all()

    return {
        "profile": {
            "id": str(student_profile.id),
            "full_name": student_profile.full_name,
            "onboarding_completed": student_profile.onboarding_completed,
            "consent_settings": student_profile.consent_settings,
        },
        "resumes": [{"id": str(r.id), "filename": r.original_filename, "uploaded_at": r.uploaded_at.isoformat()} for r in resumes],
        "job_descriptions": [{"id": str(j.id), "title": j.title, "company": j.company} for j in job_descriptions],
        "skill_evidence": [
            {
                "id": str(e.id),
                "evidence_type": e.evidence_type,
                "normalized_score": float(e.normalized_score),
                "confidence": float(e.confidence),
                "explanation": e.explanation,
                "created_at": e.created_at.isoformat(),
            }
            for e in evidence
        ],
        "career_twin_snapshots": [
            {"id": str(s.id), "version": s.version, "overall_score": float(s.overall_score) if s.overall_score is not None else None, "created_at": s.created_at.isoformat()}
            for s in snapshots
        ],
        "missions": [{"id": str(m.id), "title": m.title, "status": m.status} for m in missions],
        "assessment_attempts": [{"id": str(a.id), "status": a.status, "score": float(a.score) if a.score is not None else None} for a in assessments],
        "interview_sessions": [
            {"id": str(i.id), "mode": i.mode, "status": i.status, "overall_score": float(i.overall_score) if i.overall_score is not None else None}
            for i in interviews
        ],
        "experiment_scenarios": [{"id": str(s.id), "name": s.name} for s in scenarios],
        "audit_events": [{"id": str(a.id), "event_type": a.event_type, "created_at": a.created_at.isoformat()} for a in audit_events],
    }


def delete_interview_audio(db: Session, student_profile: StudentProfile) -> int:
    """Deletes stored audio files (and clears the pointer) for every
    interview answer belonging to this student. Transcripts are kept --
    this control is specifically audio-consent withdrawal, not a full
    account deletion."""
    answers = db.scalars(select(InterviewAnswer).join(InterviewAnswer.question)).all()
    deleted = 0
    for answer in answers:
        if answer.audio_storage_path is None:
            continue
        if answer.question.session.student_profile_id != student_profile.id:
            continue
        settings = get_settings()
        path = settings.upload_dir / answer.audio_storage_path
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass
        answer.audio_storage_path = None
        answer.audio_mime_type = None
        deleted += 1
    db.commit()
    return deleted


def delete_account(db: Session, user_id: uuid.UUID) -> None:
    """Full self-service account deletion. Every child table cascades via
    ondelete=CASCADE (StudentProfile -> resumes, evidence, snapshots,
    missions, assessments, interviews, experiments, audit events)."""
    user = db.get(User, user_id)
    if user is None:
        return
    storage_dir = get_settings().upload_dir / (str(user.student_profile.id) if user.student_profile else "")
    db.delete(user)
    db.commit()
    if user.student_profile and storage_dir.exists():
        import shutil

        shutil.rmtree(storage_dir, ignore_errors=True)
