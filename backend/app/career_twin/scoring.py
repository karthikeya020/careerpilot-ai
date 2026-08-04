"""Deterministic Career Twin scoring engine.

See docs/implementation/CAREER_TWIN_SCORING.md for the full formula writeup.
Every call to `recompute_twin` is a pure function of the `SkillEvidence` rows
currently stored for a student -- it never invents a number for a component
with no evidence, and it always writes a paired DecisionTrace + AuditEvent so
the update is traceable end to end.
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.audit import AuditEvent, DecisionTrace
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
from app.models.skill import (
    EVIDENCE_TYPE_ASSESSMENT,
    EVIDENCE_TYPE_JOB_MATCH,
    EVIDENCE_TYPE_PROJECT,
    Skill,
    SkillEvidence,
)
from app.models.student import StudentProfile
from app.schemas.career_twin import CareerTwinSnapshotOut, ReadinessComponentOut

SCORING_RULE_VERSION = "twin-v1"

# How many evidence items a component needs before confidence saturates to
# the raw evidence-weighted average. Fewer items scale confidence down
# proportionally -- one confident data point should not read as certainty.
EVIDENCE_SATURATION = {
    COMPONENT_RESUME: 3,
    COMPONENT_TECHNICAL: 4,
    COMPONENT_COMMUNICATION: 3,
    COMPONENT_ASSESSMENT: 3,
    COMPONENT_PORTFOLIO: 2,
    COMPONENT_ROLE_ALIGNMENT: 3,
}

COMPONENT_EXPLANATIONS_EMPTY = {
    COMPONENT_RESUME: "No resume has been uploaded and parsed yet.",
    COMPONENT_TECHNICAL: "No technical skill evidence found in resume, projects, or self-assessment yet.",
    COMPONENT_COMMUNICATION: "No communication/soft-skill evidence found yet.",
    COMPONENT_ASSESSMENT: "No technical assessments completed yet. Take an adaptive assessment to build this component.",
    COMPONENT_PORTFOLIO: "No project evidence found in the resume's Projects section yet.",
    COMPONENT_ROLE_ALIGNMENT: "No job description has been matched against the resume yet.",
}


@dataclass
class ComponentResult:
    component_type: str
    status: str
    score: float | None
    confidence: float | None
    evidence_count: int
    evidence_ids: list[str]
    explanation: str


def _score_component(component_type: str, evidence: list[SkillEvidence]) -> ComponentResult:
    if not evidence:
        return ComponentResult(
            component_type=component_type,
            status=STATUS_INSUFFICIENT_EVIDENCE,
            score=None,
            confidence=None,
            evidence_count=0,
            evidence_ids=[],
            explanation=COMPONENT_EXPLANATIONS_EMPTY[component_type],
        )

    total_weight = sum(float(e.weight) for e in evidence) or 1.0
    weighted_score = sum(float(e.normalized_score) * float(e.weight) for e in evidence) / total_weight
    raw_confidence = sum(float(e.confidence) * float(e.weight) for e in evidence) / total_weight
    saturation = EVIDENCE_SATURATION[component_type]
    volume_factor = min(1.0, len(evidence) / saturation)
    final_confidence = round(raw_confidence * volume_factor, 4)

    explanation = (
        f"Derived from {len(evidence)} evidence item(s) with a weighted average score of "
        f"{round(weighted_score, 2)} and raw confidence {round(raw_confidence, 2)}, scaled by an "
        f"evidence-volume factor of {round(volume_factor, 2)} (saturates at {saturation} items)."
    )

    return ComponentResult(
        component_type=component_type,
        status=STATUS_SCORED,
        score=round(weighted_score, 4),
        confidence=final_confidence,
        evidence_count=len(evidence),
        evidence_ids=[str(e.id) for e in evidence],
        explanation=explanation,
    )


def _compute_components(db: Session, student_profile_id: uuid.UUID) -> list[ComponentResult]:
    evidence_rows = db.scalars(
        select(SkillEvidence)
        .where(SkillEvidence.student_profile_id == student_profile_id)
        .join(Skill, Skill.id == SkillEvidence.skill_id)
    ).all()

    skill_by_id = {row.skill_id: row.skill for row in evidence_rows}

    resume_evidence = [e for e in evidence_rows if e.source_object_type in ("resume", "resume_section")]
    project_evidence = [e for e in evidence_rows if e.evidence_type == EVIDENCE_TYPE_PROJECT]
    technical_evidence = [
        e for e in evidence_rows if skill_by_id[e.skill_id].category in ("technical", "tools")
    ]
    communication_evidence = [
        e for e in evidence_rows if skill_by_id[e.skill_id].category in ("communication", "soft_skill")
    ]
    role_alignment_evidence = [e for e in evidence_rows if e.evidence_type == EVIDENCE_TYPE_JOB_MATCH]
    assessment_evidence = [e for e in evidence_rows if e.evidence_type == EVIDENCE_TYPE_ASSESSMENT]

    return [
        _score_component(COMPONENT_RESUME, resume_evidence),
        _score_component(COMPONENT_TECHNICAL, technical_evidence),
        _score_component(COMPONENT_COMMUNICATION, communication_evidence),
        _score_component(COMPONENT_ASSESSMENT, assessment_evidence),
        _score_component(COMPONENT_PORTFOLIO, project_evidence),
        _score_component(COMPONENT_ROLE_ALIGNMENT, role_alignment_evidence),
    ]


def recompute_twin(db: Session, student_profile: StudentProfile, reason: str) -> CareerTwinSnapshot:
    components = _compute_components(db, student_profile.id)

    scored = [c for c in components if c.status == STATUS_SCORED]
    scored_scores = [c.score for c in scored if c.score is not None]
    scored_confidences = [c.confidence for c in scored if c.confidence is not None]
    if scored_scores:
        overall_score = round(sum(scored_scores) / len(scored_scores), 4)
        coverage = len(scored) / len(ALL_COMPONENTS)
        overall_confidence = (
            round((sum(scored_confidences) / len(scored_confidences)) * coverage, 4) if scored_confidences else None
        )
    else:
        overall_score = None
        overall_confidence = None

    previous = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    previous_version = previous.version if previous is not None else None
    next_version = (previous_version + 1) if previous_version is not None else 1

    score_delta = None
    if previous is not None and previous.overall_score is not None and overall_score is not None:
        score_delta = round(overall_score - float(previous.overall_score), 4)

    change_lines = [reason]
    if score_delta is not None:
        direction = "up" if score_delta >= 0 else "down"
        change_lines.append(
            f"Overall readiness moved {direction} by {abs(score_delta)} since version {previous_version}."
        )
    elif previous is None:
        change_lines.append("This is the first Career Twin snapshot for this student.")

    snapshot = CareerTwinSnapshot(
        student_profile_id=student_profile.id,
        version=next_version,
        overall_score=overall_score,
        overall_confidence=overall_confidence,
        evidence_count=sum(c.evidence_count for c in components),
        formula_version=SCORING_RULE_VERSION,
        change_summary=" ".join(change_lines),
        score_delta=score_delta,
        previous_snapshot_id=previous.id if previous else None,
    )
    db.add(snapshot)
    db.flush()

    all_evidence_ids: list[str] = []
    for c in components:
        db.add(
            ReadinessComponent(
                snapshot_id=snapshot.id,
                component_type=c.component_type,
                score=c.score,
                confidence=c.confidence,
                status=c.status,
                evidence_count=c.evidence_count,
                explanation=c.explanation,
                evidence_ids=c.evidence_ids,
            )
        )
        all_evidence_ids.extend(c.evidence_ids)

    db.add(
        DecisionTrace(
            student_profile_id=student_profile.id,
            task_type="career_twin_update",
            route="deterministic_rule",
            confidence=overall_confidence or 0.0,
            agreement=None,
            evidence_ids=all_evidence_ids,
            agents_invoked=[],
            model_versions={"scoring_formula": SCORING_RULE_VERSION},
            reasoning_summary=snapshot.change_summary,
            requires_human_review=False,
        )
    )
    db.add(
        AuditEvent(
            student_profile_id=student_profile.id,
            event_type="career_twin_updated",
            payload={
                "version": next_version,
                "overall_score": overall_score,
                "overall_confidence": overall_confidence,
                "trigger": reason,
            },
        )
    )
    db.commit()
    db.refresh(snapshot)

    from app.services.mission_service import generate_mission_for_snapshot

    generate_mission_for_snapshot(db, student_profile, snapshot)
    return snapshot


def build_career_twin_snapshot_out(db: Session, snapshot: CareerTwinSnapshot) -> CareerTwinSnapshotOut:
    """Attaches per-component `trend` (delta vs. the previous snapshot) and
    `uncertainty` (1 - confidence) -- both derived from already-stored data,
    never a new evidence source. See PHASE_2_EXECUTION_PLAN §"Career Twin
    2.0" for why these are computed on read rather than stored columns."""
    previous_by_component: dict[str, float | None] = {}
    if snapshot.previous_snapshot_id is not None:
        previous = db.get(CareerTwinSnapshot, snapshot.previous_snapshot_id)
        if previous is not None:
            previous_by_component = {
                c.component_type: (float(c.score) if c.score is not None else None) for c in previous.components
            }

    components_out = []
    for component in snapshot.components:
        current_score = float(component.score) if component.score is not None else None
        previous_score = previous_by_component.get(component.component_type)
        trend = round(current_score - previous_score, 4) if current_score is not None and previous_score is not None else None
        uncertainty = round(1 - float(component.confidence), 4) if component.confidence is not None else None
        components_out.append(
            ReadinessComponentOut(
                component_type=component.component_type,
                score=current_score,
                confidence=float(component.confidence) if component.confidence is not None else None,
                status=component.status,
                evidence_count=component.evidence_count,
                explanation=component.explanation,
                trend=trend,
                uncertainty=uncertainty,
            )
        )

    return CareerTwinSnapshotOut(
        id=snapshot.id,
        version=snapshot.version,
        overall_score=float(snapshot.overall_score) if snapshot.overall_score is not None else None,
        overall_confidence=float(snapshot.overall_confidence) if snapshot.overall_confidence is not None else None,
        evidence_count=snapshot.evidence_count,
        formula_version=snapshot.formula_version,
        change_summary=snapshot.change_summary,
        score_delta=float(snapshot.score_delta) if snapshot.score_delta is not None else None,
        created_at=snapshot.created_at,
        components=components_out,
    )
