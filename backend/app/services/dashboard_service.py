from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.scoring import build_career_twin_snapshot_out
from app.models.audit import AuditEvent
from app.models.career_twin import CareerTwinSnapshot
from app.models.skill import Skill, SkillEvidence
from app.models.student import StudentProfile
from app.schemas.audit import AuditEventOut
from app.schemas.career_twin import ReadinessComponentOut
from app.schemas.dashboard import (
    DashboardOut,
    EvidenceItemOut,
    JobDescriptionStatusOut,
    ResumeStatusOut,
    SystemTrustOut,
    TwinUpdateSummaryOut,
)
from app.schemas.mission import LearningMissionOut
from app.schemas.student import TargetRoleOut
from app.services.job_description_service import compute_match, get_job_descriptions
from app.services.mission_service import get_active_mission, pick_priority_component
from app.services.resume_service import get_latest_resume

RECENT_EVIDENCE_LIMIT = 8
RECENT_TWIN_UPDATES_LIMIT = 5
RECENT_AUDIT_LIMIT = 10


def _resume_status(db: Session, student_profile_id) -> ResumeStatusOut:
    resume = get_latest_resume(db, student_profile_id)
    if resume is None:
        return ResumeStatusOut(uploaded=False)
    skills_detected = len(resume.resume_skills)
    return ResumeStatusOut(
        uploaded=True,
        filename=resume.original_filename,
        parsing_status=resume.parsing_status,
        parsing_error=resume.parsing_error,
        skills_detected=skills_detected,
        uploaded_at=resume.uploaded_at,
    )


def _job_description_status(db: Session, student_profile: StudentProfile) -> JobDescriptionStatusOut:
    job_descriptions = get_job_descriptions(db, student_profile.id)
    if not job_descriptions:
        return JobDescriptionStatusOut(added=False)
    latest = job_descriptions[0]
    match = compute_match(db, student_profile, latest)
    return JobDescriptionStatusOut(
        added=True,
        title=latest.title,
        coverage=match.coverage,
        matched_count=len(match.matched_skills),
        partial_count=len(match.partial_skills),
        missing_count=len(match.missing_skills),
    )


def _recent_evidence(db: Session, student_profile_id) -> list[EvidenceItemOut]:
    rows = db.execute(
        select(SkillEvidence, Skill)
        .join(Skill, Skill.id == SkillEvidence.skill_id)
        .where(SkillEvidence.student_profile_id == student_profile_id)
        .order_by(SkillEvidence.created_at.desc())
        .limit(RECENT_EVIDENCE_LIMIT)
    ).all()
    return [
        EvidenceItemOut(
            id=evidence.id,
            skill_name=skill.name,
            evidence_type=evidence.evidence_type,
            normalized_score=float(evidence.normalized_score),
            confidence=float(evidence.confidence),
            explanation=evidence.explanation,
            created_at=evidence.created_at,
        )
        for evidence, skill in rows
    ]


def _recent_twin_updates(db: Session, student_profile_id) -> list[TwinUpdateSummaryOut]:
    snapshots = db.scalars(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile_id)
        .order_by(CareerTwinSnapshot.version.desc())
        .limit(RECENT_TWIN_UPDATES_LIMIT)
    ).all()
    return [
        TwinUpdateSummaryOut(
            version=s.version,
            overall_score=float(s.overall_score) if s.overall_score is not None else None,
            score_delta=float(s.score_delta) if s.score_delta is not None else None,
            change_summary=s.change_summary,
            created_at=s.created_at,
        )
        for s in snapshots
    ]


def _recent_audit_events(db: Session, student_profile_id) -> list[AuditEvent]:
    return list(
        db.scalars(
            select(AuditEvent)
            .where(AuditEvent.student_profile_id == student_profile_id)
            .order_by(AuditEvent.created_at.desc())
            .limit(RECENT_AUDIT_LIMIT)
        ).all()
    )


def build_dashboard(db: Session, student_profile: StudentProfile) -> DashboardOut:
    latest_snapshot = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    priority_weakness = pick_priority_component(latest_snapshot.components) if latest_snapshot else None
    mission = get_active_mission(db, student_profile.id)

    scored_count = 0
    total_evidence = 0
    formula_version = "twin-v1"
    if latest_snapshot:
        scored_count = sum(1 for c in latest_snapshot.components if c.status == "scored")
        total_evidence = latest_snapshot.evidence_count
        formula_version = latest_snapshot.formula_version

    return DashboardOut(
        student_name=student_profile.full_name,
        onboarding_completed=student_profile.onboarding_completed,
        target_role=(
            TargetRoleOut.model_validate(student_profile.primary_target_role)
            if student_profile.primary_target_role
            else None
        ),
        career_twin=build_career_twin_snapshot_out(db, latest_snapshot) if latest_snapshot else None,
        mission=LearningMissionOut.model_validate(mission) if mission else None,
        priority_weakness=ReadinessComponentOut.model_validate(priority_weakness) if priority_weakness else None,
        resume_status=_resume_status(db, student_profile.id),
        job_description_status=_job_description_status(db, student_profile),
        recent_evidence=_recent_evidence(db, student_profile.id),
        recent_twin_updates=_recent_twin_updates(db, student_profile.id),
        recent_audit_events=[AuditEventOut.model_validate(e) for e in _recent_audit_events(db, student_profile.id)],
        system_trust=SystemTrustOut(
            formula_version=formula_version,
            components_scored=scored_count,
            components_total=6,
            total_evidence_count=total_evidence,
        ),
    )
