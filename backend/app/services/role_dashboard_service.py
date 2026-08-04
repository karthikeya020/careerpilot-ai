"""Faculty, placement-cell, recruiter, and administrator dashboards.
Every number here is a real aggregate SQL query over stored data --
cohort-level only, never a per-student ranking, and never a hiring
probability (Constitution rules 5/6/19). Individual student identification
appears only where the role has a legitimate, narrowly-scoped need
(faculty: who needs human support; recruiter: students who explicitly
opted in) -- never as a leaderboard.
"""

import uuid
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.assessment import AssessmentAttempt
from app.models.audit import AuditEvent
from app.models.base import utcnow
from app.models.care import CareExecution
from app.models.career_twin import ALL_COMPONENTS, CareerTwinSnapshot, ReadinessComponent
from app.models.mission import MISSION_STATUS_COMPLETED, LearningMission
from app.models.student import StudentProfile
from app.models.user import ALL_ROLES, UserRole

_READINESS_BUCKETS = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]


def _latest_snapshot_subquery(db: Session):
    return (
        select(
            CareerTwinSnapshot.student_profile_id,
            func.max(CareerTwinSnapshot.version).label("max_version"),
        )
        .group_by(CareerTwinSnapshot.student_profile_id)
        .subquery()
    )


def _latest_snapshots(db: Session) -> list[CareerTwinSnapshot]:
    latest = _latest_snapshot_subquery(db)
    return list(
        db.scalars(
            select(CareerTwinSnapshot).join(
                latest,
                (CareerTwinSnapshot.student_profile_id == latest.c.student_profile_id)
                & (CareerTwinSnapshot.version == latest.c.max_version),
            )
        ).all()
    )


def get_cohort_skill_gaps(db: Session) -> list[dict]:
    """Average score per readiness component across every student's most
    recent Career Twin snapshot -- an aggregate, never an individual score."""
    snapshots = _latest_snapshots(db)
    snapshot_ids = [s.id for s in snapshots]
    if not snapshot_ids:
        return [{"component_type": c, "average_score": None, "scored_student_count": 0} for c in ALL_COMPONENTS]

    rows = db.execute(
        select(
            ReadinessComponent.component_type,
            func.avg(ReadinessComponent.score),
            func.count(ReadinessComponent.id),
        )
        .where(ReadinessComponent.snapshot_id.in_(snapshot_ids), ReadinessComponent.status == "scored")
        .group_by(ReadinessComponent.component_type)
    ).all()
    by_component = {row[0]: (float(row[1]), row[2]) for row in rows}

    return [
        {
            "component_type": component,
            "average_score": round(by_component[component][0], 4) if component in by_component else None,
            "scored_student_count": by_component[component][1] if component in by_component else 0,
        }
        for component in ALL_COMPONENTS
    ]


def get_faculty_dashboard(db: Session) -> dict:
    total_students = db.scalar(select(func.count()).select_from(StudentProfile)) or 0
    skill_gaps = get_cohort_skill_gaps(db)

    missions_total = db.scalar(select(func.count()).select_from(LearningMission)) or 0
    missions_completed = (
        db.scalar(select(func.count()).where(LearningMission.status == MISSION_STATUS_COMPLETED)) or 0
    )

    assessments_total = db.scalar(select(func.count()).select_from(AssessmentAttempt)) or 0
    assessments_completed = db.scalar(select(func.count()).where(AssessmentAttempt.status == "completed")) or 0

    students_needing_support = db.execute(
        select(StudentProfile.id, StudentProfile.full_name, func.count(CareExecution.id))
        .join(CareExecution, CareExecution.student_profile_id == StudentProfile.id)
        .where(CareExecution.requires_human_review.is_(True))
        .group_by(StudentProfile.id, StudentProfile.full_name)
    ).all()

    recent = _latest_snapshots(db)
    recent_deltas = [float(s.score_delta) for s in recent if s.score_delta is not None]
    improvement_trend = round(sum(recent_deltas) / len(recent_deltas), 4) if recent_deltas else None

    return {
        "total_students": total_students,
        "cohort_skill_gaps": skill_gaps,
        "mission_completion_rate": round(missions_completed / missions_total, 4) if missions_total else None,
        "assessment_completion_rate": round(assessments_completed / assessments_total, 4) if assessments_total else None,
        "average_readiness_trend": improvement_trend,
        "students_needing_support": [
            {"student_profile_id": str(sid), "full_name": name, "flagged_decision_count": count}
            for sid, name, count in students_needing_support
        ],
    }


def get_placement_dashboard(db: Session) -> dict:
    snapshots = _latest_snapshots(db)
    scores = [float(s.overall_score) for s in snapshots if s.overall_score is not None]

    distribution = []
    for lo, hi in _READINESS_BUCKETS:
        count = sum(1 for s in scores if lo <= s * 100 < hi)
        distribution.append({"range_start": lo, "range_end": min(hi, 100), "student_count": count})

    skill_gaps = get_cohort_skill_gaps(db)
    role_alignment = next((g for g in skill_gaps if g["component_type"] == "role_alignment_readiness"), None)

    deltas = [float(s.score_delta) for s in snapshots if s.score_delta is not None]
    program_effectiveness = round(sum(deltas) / len(deltas), 4) if deltas else None

    weakest = sorted((g for g in skill_gaps if g["average_score"] is not None), key=lambda g: g["average_score"])[:3]

    return {
        "student_count_with_snapshot": len(snapshots),
        "readiness_distribution": distribution,
        "role_alignment_average": role_alignment["average_score"] if role_alignment else None,
        "common_skill_gaps": weakest,
        "program_effectiveness_average_delta": program_effectiveness,
        "disclaimer": "Aggregate, privacy-safe readiness analytics -- not a hiring or placement guarantee.",
    }


def get_recruiter_candidates(db: Session) -> list[dict]:
    """Only students who explicitly set consent_settings.recruiter_visible
    -- never the full cohort. No automatic hiring recommendation is
    computed or included."""
    profiles = db.scalars(select(StudentProfile)).all()
    consented = [p for p in profiles if p.consent_settings.get("recruiter_visible") is True]

    candidates = []
    for profile in consented:
        snapshot = db.scalar(
            select(CareerTwinSnapshot)
            .where(CareerTwinSnapshot.student_profile_id == profile.id)
            .order_by(CareerTwinSnapshot.version.desc())
        )
        components = []
        pending_review = False
        if snapshot is not None:
            components = [
                {
                    "component_type": c.component_type,
                    "score": float(c.score) if c.score is not None else None,
                    "confidence": float(c.confidence) if c.confidence is not None else None,
                    "status": c.status,
                }
                for c in snapshot.components
            ]
            pending_review = (
                db.scalar(
                    select(func.count())
                    .select_from(CareExecution)
                    .where(
                        CareExecution.student_profile_id == profile.id,
                        CareExecution.requires_human_review.is_(True),
                    )
                )
                or 0
            ) > 0

        candidates.append(
            {
                "student_profile_id": str(profile.id),
                "full_name": profile.full_name,
                "target_role": profile.primary_target_role.title if profile.primary_target_role else None,
                "overall_score": float(snapshot.overall_score) if snapshot and snapshot.overall_score is not None else None,
                "overall_confidence": (
                    float(snapshot.overall_confidence) if snapshot and snapshot.overall_confidence is not None else None
                ),
                "components": components,
                "requires_human_review": pending_review,
                "consent_status": "explicit_opt_in",
            }
        )
    return candidates


def set_recruiter_visibility(db: Session, student_profile: StudentProfile, visible: bool) -> None:
    student_profile.consent_settings = {**student_profile.consent_settings, "recruiter_visible": visible}
    db.commit()


def get_admin_dashboard(db: Session, graph_available: bool, redis_ok: bool) -> dict:
    user_count_rows = db.execute(select(UserRole.role_id, func.count()).group_by(UserRole.role_id)).all()
    user_counts: dict[uuid.UUID, int] = {row[0]: row[1] for row in user_count_rows}

    from app.models.user import Role

    role_name_rows = db.execute(select(Role.id, Role.name)).all()
    role_names: dict[uuid.UUID, str] = {row[0]: row[1] for row in role_name_rows}
    users_by_role = {role_names.get(role_id, str(role_id)): count for role_id, count in user_counts.items()}
    for role in ALL_ROLES:
        users_by_role.setdefault(role, 0)

    total_executions = db.scalar(select(func.count()).select_from(CareExecution)) or 0
    route_count_rows = db.execute(select(CareExecution.route, func.count()).group_by(CareExecution.route)).all()
    route_counts: dict[str, int] = {row[0]: row[1] for row in route_count_rows}
    avg_confidence = db.scalar(select(func.avg(CareExecution.confidence))) if total_executions else None
    avg_latency = db.scalar(select(func.avg(CareExecution.latency_ms))) if total_executions else None
    avg_cost = db.scalar(select(func.avg(CareExecution.cost_usd))) if total_executions else None
    human_review_count = db.scalar(select(func.count()).where(CareExecution.requires_human_review.is_(True))) or 0

    recent_window = utcnow() - timedelta(days=7)
    recent_audit_events = db.scalars(
        select(AuditEvent).where(AuditEvent.created_at >= recent_window).order_by(AuditEvent.created_at.desc()).limit(20)
    ).all()

    return {
        "service_health": {
            "database": True,  # this query itself succeeding proves DB connectivity
            "redis": redis_ok,
            "neo4j": graph_available,
        },
        "users_by_role": users_by_role,
        "total_users": sum(users_by_role.values()),
        "care_execution_stats": {
            "total_executions": total_executions,
            "route_frequency": route_counts,
            "average_confidence": round(float(avg_confidence), 4) if avg_confidence is not None else None,
            "average_latency_ms": round(float(avg_latency), 3) if avg_latency is not None else None,
            "average_cost_usd": round(float(avg_cost), 6) if avg_cost is not None else None,
            "human_review_rate": round(human_review_count / total_executions, 4) if total_executions else None,
        },
        "recent_audit_events": [
            {"id": str(e.id), "event_type": e.event_type, "created_at": e.created_at.isoformat()}
            for e in recent_audit_events
        ],
    }
