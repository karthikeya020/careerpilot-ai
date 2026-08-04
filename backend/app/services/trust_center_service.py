"""Trust Center: read-only queries over CareExecution/AgentRun (the CARE
engine's own execution log, see app/care_engine/engine.py) plus a Career
Twin change explanation derived from stored snapshot deltas. Nothing here
computes a new number -- it only surfaces what was already persisted at
decision time, which is the whole point of a trust layer (Constitution
rule 3/4).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.care import CareExecution
from app.models.career_twin import CareerTwinSnapshot, ReadinessComponent


def list_executions(db: Session, student_profile_id: uuid.UUID, limit: int = 20) -> list[CareExecution]:
    return list(
        db.scalars(
            select(CareExecution)
            .where(CareExecution.student_profile_id == student_profile_id)
            .order_by(CareExecution.created_at.desc())
            .limit(limit)
        ).all()
    )


def get_execution_detail(db: Session, execution_id: uuid.UUID) -> CareExecution | None:
    return db.get(CareExecution, execution_id)


def explain_twin_change(db: Session, snapshot: CareerTwinSnapshot) -> dict:
    """Component-by-component diff against the previous snapshot, so 'why
    did my score change' always has a concrete, evidence-traceable answer
    instead of just the free-text `change_summary`."""
    previous_components: dict[str, ReadinessComponent] = {}
    if snapshot.previous_snapshot_id is not None:
        previous_snapshot = db.get(CareerTwinSnapshot, snapshot.previous_snapshot_id)
        if previous_snapshot is not None:
            previous_components = {c.component_type: c for c in previous_snapshot.components}

    component_diffs = []
    for component in snapshot.components:
        previous = previous_components.get(component.component_type)
        previous_score = float(previous.score) if previous and previous.score is not None else None
        current_score = float(component.score) if component.score is not None else None
        delta = None
        if previous_score is not None and current_score is not None:
            delta = round(current_score - previous_score, 4)
        component_diffs.append(
            {
                "component_type": component.component_type,
                "previous_score": previous_score,
                "current_score": current_score,
                "delta": delta,
                "evidence_count": component.evidence_count,
                "evidence_ids": component.evidence_ids,
                "explanation": component.explanation,
            }
        )

    return {
        "snapshot_id": str(snapshot.id),
        "version": snapshot.version,
        "overall_score": float(snapshot.overall_score) if snapshot.overall_score is not None else None,
        "overall_confidence": float(snapshot.overall_confidence) if snapshot.overall_confidence is not None else None,
        "score_delta": float(snapshot.score_delta) if snapshot.score_delta is not None else None,
        "change_summary": snapshot.change_summary,
        "formula_version": snapshot.formula_version,
        "component_diffs": component_diffs,
    }
