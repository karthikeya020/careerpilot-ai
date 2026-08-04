from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.scoring import recompute_twin
from app.models.audit import AuditEvent
from app.models.skill import EVIDENCE_TYPE_SELF_ASSESSMENT, SkillEvidence, StudentSkill
from app.models.student import CareerGoal, StudentProfile, TargetRole
from app.schemas.onboarding import OnboardingRequest
from app.services.skill_matching import find_skill_by_name


def _apply_self_assessment(db: Session, student_profile: StudentProfile, skill_name: str, rating: float) -> bool:
    skill = find_skill_by_name(db, skill_name)
    if skill is None:
        return False

    student_skill = db.scalar(
        select(StudentSkill).where(
            StudentSkill.student_profile_id == student_profile.id, StudentSkill.skill_id == skill.id
        )
    )
    if student_skill is None:
        student_skill = StudentSkill(student_profile_id=student_profile.id, skill_id=skill.id, self_rating=rating)
        db.add(student_skill)
    else:
        student_skill.self_rating = rating

    db.add(
        SkillEvidence(
            student_profile_id=student_profile.id,
            skill_id=skill.id,
            evidence_type=EVIDENCE_TYPE_SELF_ASSESSMENT,
            source_object_type="student_profile",
            source_object_id=student_profile.id,
            raw_score=rating,
            normalized_score=rating,
            weight=0.5,
            confidence=0.4,
            explanation=f"Student self-reported proficiency in {skill.name} during onboarding.",
        )
    )
    return True


def complete_onboarding(db: Session, student_profile: StudentProfile, payload: OnboardingRequest) -> StudentProfile:
    student_profile.full_name = payload.full_name
    student_profile.consent_settings = {"data_processing": payload.consent_data_processing}
    student_profile.onboarding_completed = True

    db.add(
        CareerGoal(
            student_profile_id=student_profile.id,
            description=payload.career_goal_description,
            timeline_months=payload.timeline_months,
        )
    )

    for existing in student_profile.target_roles:
        existing.is_primary = False
    target_role = TargetRole(
        student_profile_id=student_profile.id,
        title=payload.target_role_title,
        seniority=payload.target_role_seniority,
        is_primary=True,
    )
    db.add(target_role)
    db.flush()
    student_profile.primary_target_role_id = target_role.id

    matched_skills = []
    unmatched_skills = []
    for entry in payload.self_assessed_skills:
        if _apply_self_assessment(db, student_profile, entry.skill_name, entry.rating):
            matched_skills.append(entry.skill_name)
        else:
            unmatched_skills.append(entry.skill_name)

    db.add(
        AuditEvent(
            student_profile_id=student_profile.id,
            event_type="onboarding_completed",
            payload={
                "target_role": payload.target_role_title,
                "matched_self_assessed_skills": matched_skills,
                "unmatched_self_assessed_skills": unmatched_skills,
            },
        )
    )
    db.commit()
    db.refresh(student_profile)

    recompute_twin(db, student_profile, reason="Onboarding completed: target role and self-assessment recorded.")
    db.refresh(student_profile)
    return student_profile
