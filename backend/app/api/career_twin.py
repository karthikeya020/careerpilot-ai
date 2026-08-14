import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.multi_role import score_multi_role_alignment
from app.career_twin.projection import TARGET_READINESS, project_time_to_target
from app.career_twin.proof import build_snapshot_proof
from app.career_twin.scoring import build_career_twin_snapshot_out
from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.career_twin import CareerTwinSnapshot
from app.models.student import StudentProfile
from app.schemas.career_twin import (
    CareerTwinSnapshotOut,
    ComponentProjectionOut,
    ComponentProofOut,
    EvidenceCitationOut,
    RoleAlignmentOut,
    SnapshotProofOut,
)

router = APIRouter(prefix="/career-twin", tags=["career-twin"])


@router.get("", response_model=CareerTwinSnapshotOut)
def get_latest_snapshot(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> CareerTwinSnapshotOut:
    snapshot = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    if snapshot is None:
        raise NotFoundError("No Career Twin snapshot yet. Complete onboarding to generate one.")
    return build_career_twin_snapshot_out(db, snapshot)


@router.get("/history", response_model=list[CareerTwinSnapshotOut])
def get_snapshot_history(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[CareerTwinSnapshotOut]:
    snapshots = db.scalars(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    ).all()
    return [build_career_twin_snapshot_out(db, s) for s in snapshots]


@router.get("/multi-role", response_model=list[RoleAlignmentOut])
def get_multi_role_alignment(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[RoleAlignmentOut]:
    alignments = score_multi_role_alignment(db, student_profile.id)
    return [RoleAlignmentOut(**vars(a)) for a in alignments]


@router.get("/time-to-target", response_model=list[ComponentProjectionOut])
def get_time_to_target(
    target: float = Query(TARGET_READINESS, ge=0.0, le=1.0),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[ComponentProjectionOut]:
    projections = project_time_to_target(db, student_profile.id, target=target)
    return [ComponentProjectionOut(**vars(p)) for p in projections]


@router.get("/{snapshot_id}/proof", response_model=SnapshotProofOut)
def get_snapshot_proof(
    snapshot_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> SnapshotProofOut:
    snapshot = db.scalar(
        select(CareerTwinSnapshot).where(
            CareerTwinSnapshot.id == snapshot_id, CareerTwinSnapshot.student_profile_id == student_profile.id
        )
    )
    if snapshot is None:
        raise NotFoundError("Snapshot not found.")
    proof = build_snapshot_proof(db, student_profile, snapshot)
    return SnapshotProofOut(
        student_name=proof.student_name,
        target_role=proof.target_role,
        version=proof.version,
        created_at=proof.created_at,
        overall_score=proof.overall_score,
        overall_confidence=proof.overall_confidence,
        formula_version=proof.formula_version,
        disclaimer=proof.disclaimer,
        components=[
            ComponentProofOut(
                component_type=c.component_type,
                score=c.score,
                confidence=c.confidence,
                status=c.status,
                evidence_count=c.evidence_count,
                citations=[
                    EvidenceCitationOut(
                        skill_name=cite.skill_name,
                        evidence_type=cite.evidence_type,
                        explanation=cite.explanation,
                        created_at=cite.created_at,
                    )
                    for cite in c.citations
                ],
            )
            for c in proof.components
        ],
    )
