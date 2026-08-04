import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.career_twin import (
    ALL_COMPONENTS,
    COMPONENT_ASSESSMENT,
    COMPONENT_COMMUNICATION,
    COMPONENT_PORTFOLIO,
    COMPONENT_RESUME,
    COMPONENT_ROLE_ALIGNMENT,
    COMPONENT_TECHNICAL,
    STATUS_INSUFFICIENT_EVIDENCE,
    STATUS_SCORED,
    CareerTwinSnapshot,
    ReadinessComponent,
)
from app.models.mission import MISSION_STATUS_DISMISSED, MISSION_STATUS_PENDING, LearningMission
from app.models.skill import EVIDENCE_TYPE_ASSESSMENT, Skill, SkillEvidence
from app.models.student import StudentProfile

_ACTIONABLE_COMPONENTS = [c for c in ALL_COMPONENTS if c != COMPONENT_ASSESSMENT]

_INSUFFICIENT_EVIDENCE_MISSIONS = {
    COMPONENT_RESUME: (
        "Upload your resume",
        (
            "Your Career Twin can't assess resume or technical readiness yet. Upload a resume (PDF or DOCX) "
            "to generate your first evidence-backed skill profile."
        ),
    ),
    COMPONENT_TECHNICAL: (
        "Add technical evidence",
        (
            "No technical skill evidence found yet. Upload a resume or rate your skills during onboarding to "
            "start building technical readiness."
        ),
    ),
    COMPONENT_COMMUNICATION: (
        "Add communication evidence",
        (
            "No communication or soft-skill evidence found yet. Mention relevant experience (presentations, "
            "writing, teamwork) in your resume to build this component."
        ),
    ),
    COMPONENT_PORTFOLIO: (
        "Add a project to your resume",
        (
            "No project evidence found yet. Add a Projects section to your resume describing something you "
            "built, with the tools and skills you used."
        ),
    ),
    COMPONENT_ROLE_ALIGNMENT: (
        "Add a target job description",
        (
            "Add a job description for a role you're targeting so your Career Twin can measure alignment "
            "against real requirements."
        ),
    ),
}


def _weakest_evidence_for_component(
    db: Session, student_profile_id: uuid.UUID, component: ReadinessComponent
) -> SkillEvidence | None:
    if not component.evidence_ids:
        return None
    evidence_rows = db.scalars(
        select(SkillEvidence).where(SkillEvidence.id.in_([uuid.UUID(e) for e in component.evidence_ids]))
    ).all()
    if not evidence_rows:
        return None
    return min(evidence_rows, key=lambda e: float(e.normalized_score))


def _weakest_skill_for_component(db: Session, student_profile_id: uuid.UUID, component: ReadinessComponent):
    weakest = _weakest_evidence_for_component(db, student_profile_id, component)
    if weakest is None:
        return None
    return db.get(Skill, weakest.skill_id)


def pick_priority_component(components: list[ReadinessComponent]) -> ReadinessComponent:
    actionable = [c for c in components if c.component_type in _ACTIONABLE_COMPONENTS]
    scored = [c for c in actionable if c.status == STATUS_SCORED]
    if scored:
        return min(scored, key=lambda c: float(c.score) if c.score is not None else 0.0)

    insufficient = [c for c in actionable if c.status == STATUS_INSUFFICIENT_EVIDENCE]
    resume_first = next((c for c in insufficient if c.component_type == COMPONENT_RESUME), None)
    return resume_first or insufficient[0]


def generate_mission_for_snapshot(
    db: Session, student_profile: StudentProfile, snapshot: CareerTwinSnapshot
) -> LearningMission:
    priority = pick_priority_component(snapshot.components)

    target_skill = None
    if priority.status == STATUS_SCORED and priority.component_type in (
        COMPONENT_TECHNICAL,
        COMPONENT_COMMUNICATION,
        COMPONENT_PORTFOLIO,
    ):
        target_skill = _weakest_skill_for_component(db, student_profile.id, priority)

    # Autonomous-loop root-cause enrichment (Diagnose/Plan/Teach): a fresh
    # incorrect assessment answer is timely, specific, actionable evidence --
    # it takes precedence over the generic priority-component template even
    # when the assessed component isn't this snapshot's single lowest-scoring
    # one, because "you just got this wrong, here's why and what to do about
    # it" is more useful than a generic "your weakest area is X" template.
    # Falls back to the priority component's weakest evidence if the most
    # recent evidence isn't a fresh assessment miss. See
    # app/services/autonomous_loop_service.py.
    #
    # A single call to complete_attempt() can record several SkillEvidence
    # rows (one per question answered) with an identical created_at
    # timestamp -- when that happens, prefer an incorrect one over a correct
    # one as the "most recent" signal, since explaining a miss is more
    # actionable than explaining a hit.
    root_cause_plan = None
    latest_created_at = db.scalar(
        select(func.max(SkillEvidence.created_at)).where(SkillEvidence.student_profile_id == student_profile.id)
    )
    candidate_evidence = None
    if latest_created_at is not None:
        latest_batch = db.scalars(
            select(SkillEvidence).where(
                SkillEvidence.student_profile_id == student_profile.id,
                SkillEvidence.created_at == latest_created_at,
                SkillEvidence.evidence_type == EVIDENCE_TYPE_ASSESSMENT,
            )
        ).all()
        incorrect_in_batch = [e for e in latest_batch if float(e.normalized_score) < 0.5]
        if incorrect_in_batch:
            candidate_evidence = incorrect_in_batch[0]
        elif latest_batch:
            candidate_evidence = latest_batch[0]
    if candidate_evidence is None and priority.status == STATUS_SCORED:
        candidate_evidence = _weakest_evidence_for_component(db, student_profile.id, priority)

    if candidate_evidence is not None:
        from app.services.autonomous_loop_service import build_root_cause_mission_plan

        root_cause_plan = build_root_cause_mission_plan(
            db, student_profile, candidate_evidence, priority.component_type
        )

    if root_cause_plan is not None:
        title = root_cause_plan.title
        description = root_cause_plan.description
    elif priority.status == STATUS_INSUFFICIENT_EVIDENCE:
        title, description = _INSUFFICIENT_EVIDENCE_MISSIONS[priority.component_type]
    elif target_skill is not None:
        title = f"Strengthen {target_skill.name}"
        description = (
            f"Your weakest evidence in {priority.component_type.replace('_', ' ')} is '{target_skill.name}'. "
            f"Build or contribute to a small project that clearly demonstrates {target_skill.name}, then "
            "update your resume with the details."
        )
    else:
        title = f"Improve {priority.component_type.replace('_', ' ')}"
        description = priority.explanation

    # Keep exactly one active mission: superseding an update should not pile
    # up stale "today's mission" rows.
    stale_missions = db.scalars(
        select(LearningMission).where(
            LearningMission.student_profile_id == student_profile.id,
            LearningMission.status == MISSION_STATUS_PENDING,
        )
    ).all()
    for stale in stale_missions:
        stale.status = MISSION_STATUS_DISMISSED

    mission = LearningMission(
        student_profile_id=student_profile.id,
        title=title,
        description=description,
        target_skill_id=target_skill.id if target_skill else None,
        target_concept_id=root_cause_plan.target_concept_id if root_cause_plan else None,
        source_component=priority.component_type,
        priority_rank=1,
        status=MISSION_STATUS_PENDING,
        evidence_ids=priority.evidence_ids,
        tasks=root_cause_plan.tasks if root_cause_plan else [],
        estimated_minutes=root_cause_plan.estimated_minutes if root_cause_plan else None,
        root_cause=root_cause_plan.root_cause if root_cause_plan else None,
        resource_ids=root_cause_plan.resource_ids if root_cause_plan else [],
        expected_impact_estimate=root_cause_plan.expected_impact_estimate if root_cause_plan else None,
        expected_impact_confidence=root_cause_plan.expected_impact_confidence if root_cause_plan else None,
    )
    db.add(mission)
    db.commit()
    db.refresh(mission)
    return mission


def get_active_mission(db: Session, student_profile_id: uuid.UUID) -> LearningMission | None:
    return db.scalar(
        select(LearningMission)
        .where(
            LearningMission.student_profile_id == student_profile_id,
            LearningMission.status == MISSION_STATUS_PENDING,
        )
        .order_by(LearningMission.created_at.desc())
    )
