"""Deterministic Career Twin scoring engine.

See docs/implementation/CAREER_TWIN_SCORING.md for the full formula writeup.
Every call to `recompute_twin` is a pure function of the `SkillEvidence` rows
currently stored for a student -- it never invents a number for a component
with no evidence, and it always writes a paired DecisionTrace + AuditEvent so
the update is traceable end to end.
"""

import statistics
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.base import utcnow

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
    SkillEvidence,
)
from app.models.student import StudentProfile
from app.schemas.career_twin import CareerTwinSnapshotOut, ReadinessComponentOut, RippleNoteOut
from app.services.evidence_service import get_active_skill_evidence

SCORING_RULE_VERSION = "twin-v2"

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

# --- twin-v2 small-sample safeguard -----------------------------------
# A single session (e.g. two interview answers) must never read as a
# confidently established skill level. Three independent levers enforce
# this, all deterministic and versioned here (see
# docs/implementation/CAREER_TWIN_SCORING.md "Small-sample safeguard"):
#
# 1. Evidence-diversity weighting: evidence repeated from a single
#    `source_object_type` (e.g. five answers in one interview session)
#    counts less than the same volume spread across independent sources
#    (interview + resume + assessment). `diversity_factor` captures this.
# 2. Prior-weighted (shrinkage) scoring: the displayed score is pulled
#    toward a neutral 0.5 prior in proportion to how little it can be
#    trusted (`trust_factor = volume_factor * diversity_factor`) -- a
#    perfect 0.9 raw score from one narrow session reports well below 0.9,
#    not at face value.
# 3. Hard confidence cap: below the minimum evidence count or source
#    diversity, confidence is capped outright regardless of how high the
#    raw evidence confidence was, and `is_low_sample` is set so the UI can
#    render an explicit "more evidence needed" notice.
#
# A fourth, independent signal -- internal disagreement across evidence
# items (population stdev of normalized_score) -- further discounts
# confidence when evidence for the same component actively conflicts.
MIN_EVIDENCE_FOR_STABLE_CONFIDENCE = 3
MIN_SOURCE_DIVERSITY_TARGET = 2
LOW_SAMPLE_CONFIDENCE_CAP = 0.50
NEUTRAL_SCORE_PRIOR = 0.50
HIGH_DISAGREEMENT_THRESHOLD = 0.25

LOW_SAMPLE_NOTICE = (
    "Strong performance in this session, but more evidence is required to establish long-term proficiency."
)
CONFLICTING_EVIDENCE_NOTICE = (
    "Evidence for this component disagrees significantly across sources -- "
    "treat this score as provisional until more consistent evidence accumulates."
)

# --- twin-v2 evidence-freshness safeguard -------------------------------
# Same philosophy as the small-sample safeguard above, applied to time
# instead of sample size: evidence doesn't stay equally trustworthy
# forever. Each evidence item's contribution to the weighted average decays
# continuously with age (half-life below), and if a majority of a
# component's evidence has crossed the staleness threshold, confidence is
# capped outright and the explanation says so plainly -- never a silent
# score that quietly drifts stale.
EVIDENCE_FRESHNESS_HALF_LIFE_DAYS = 180.0  # ~6 months
EVIDENCE_FRESHNESS_FLOOR = 0.4  # old evidence is still real evidence -- never discounted to zero
STALE_EVIDENCE_AGE_DAYS = 180.0  # ~6 months, matches the half-life
STALE_FRACTION_CAP_THRESHOLD = 0.5  # majority of evidence (by count) is stale
STALE_EVIDENCE_CONFIDENCE_CAP = 0.60


def _freshness_multiplier(evidence: SkillEvidence, now) -> float:
    age_days = max(0.0, (now - evidence.created_at).total_seconds() / 86400)
    decayed = 0.5 ** (age_days / EVIDENCE_FRESHNESS_HALF_LIFE_DAYS)
    return max(EVIDENCE_FRESHNESS_FLOOR, decayed)

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
    evidence_diversity: int = 0
    is_low_sample: bool = False
    stale_evidence_fraction: float = 0.0
    is_stale_evidence: bool = False


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

    now = utcnow()
    freshness_by_id = {e.id: _freshness_multiplier(e, now) for e in evidence}
    effective_weight_by_id = {e.id: float(e.weight) * freshness_by_id[e.id] for e in evidence}

    total_weight = sum(effective_weight_by_id.values()) or 1.0
    raw_weighted_score = sum(float(e.normalized_score) * effective_weight_by_id[e.id] for e in evidence) / total_weight
    raw_confidence = sum(float(e.confidence) * effective_weight_by_id[e.id] for e in evidence) / total_weight
    saturation = EVIDENCE_SATURATION[component_type]
    volume_factor = min(1.0, len(evidence) / saturation)

    stale_count = sum(
        1 for e in evidence if (now - e.created_at).total_seconds() / 86400 >= STALE_EVIDENCE_AGE_DAYS
    )
    stale_evidence_fraction = round(stale_count / len(evidence), 4)
    is_stale_evidence = stale_evidence_fraction > STALE_FRACTION_CAP_THRESHOLD

    distinct_sources = len({e.source_object_type for e in evidence})
    diversity_factor = min(1.0, distinct_sources / MIN_SOURCE_DIVERSITY_TARGET)
    trust_factor = volume_factor * diversity_factor

    scores = [float(e.normalized_score) for e in evidence]
    disagreement = round(statistics.pstdev(scores), 4) if len(scores) > 1 else 0.0
    conflicting = disagreement > HIGH_DISAGREEMENT_THRESHOLD

    # Prior-weighted shrinkage: sparse and/or single-source evidence is
    # pulled toward a neutral prior instead of letting a couple of items
    # alone claim an extreme score.
    score = round(raw_weighted_score * trust_factor + NEUTRAL_SCORE_PRIOR * (1 - trust_factor), 4)

    confidence = raw_confidence * volume_factor * diversity_factor
    if conflicting:
        confidence *= 1 - disagreement

    is_low_sample = len(evidence) < MIN_EVIDENCE_FOR_STABLE_CONFIDENCE or distinct_sources < MIN_SOURCE_DIVERSITY_TARGET
    if is_low_sample:
        confidence = min(confidence, LOW_SAMPLE_CONFIDENCE_CAP)
    if is_stale_evidence:
        confidence = min(confidence, STALE_EVIDENCE_CONFIDENCE_CAP)
    confidence = round(confidence, 4)

    explanation_parts = [
        (
            f"Derived from {len(evidence)} evidence item(s) from {distinct_sources} distinct source(s), "
            f"raw weighted score {round(raw_weighted_score, 2)}, raw confidence {round(raw_confidence, 2)}, "
            f"shrunk toward a neutral prior by a trust factor of {round(trust_factor, 2)} "
            f"(volume {round(volume_factor, 2)} x diversity {round(diversity_factor, 2)})."
        )
    ]
    if conflicting:
        explanation_parts.append(f"{CONFLICTING_EVIDENCE_NOTICE} (disagreement {disagreement}).")
    if is_low_sample:
        explanation_parts.append(LOW_SAMPLE_NOTICE)
    if is_stale_evidence:
        explanation_parts.append(
            f"This component's confidence is capped because {round(stale_evidence_fraction * 100)}% "
            "of its evidence is 6+ months old."
        )

    return ComponentResult(
        component_type=component_type,
        status=STATUS_SCORED,
        score=score,
        confidence=confidence,
        evidence_count=len(evidence),
        evidence_ids=[str(e.id) for e in evidence],
        explanation=" ".join(explanation_parts),
        stale_evidence_fraction=stale_evidence_fraction,
        is_stale_evidence=is_stale_evidence,
        evidence_diversity=distinct_sources,
        is_low_sample=is_low_sample,
    )


def _compute_components(db: Session, student_profile_id: uuid.UUID) -> list[ComponentResult]:
    # Excludes resume-sourced evidence tied to a superseded resume version --
    # see app/services/evidence_service.py. Career Twin scoring must always
    # be a pure function of *currently active* evidence, never stale data
    # from a resume the student has since replaced.
    evidence_rows = get_active_skill_evidence(db, student_profile_id)

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
                evidence_diversity=c.evidence_diversity,
                is_low_sample=c.is_low_sample,
                stale_evidence_fraction=c.stale_evidence_fraction,
                is_stale_evidence=c.is_stale_evidence,
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


MILESTONE_SCORE_THRESHOLD = 0.70


def _component_provenance(db: Session, evidence_ids: list[str]) -> dict[str, float]:
    """This component's evidence weight, broken down by evidence_type and
    normalized to fractions that sum to ~1.0 -- e.g. {"technical_assessment":
    0.4, "interview": 0.35, "resume": 0.25}. Re-fetches the SkillEvidence
    rows the component was already scored from (via its stored evidence_ids)
    rather than storing a duplicate breakdown, same "derived, not stored"
    pattern as trend/uncertainty above."""
    if not evidence_ids:
        return {}
    ids = [uuid.UUID(eid) for eid in evidence_ids]
    rows = db.scalars(select(SkillEvidence).where(SkillEvidence.id.in_(ids))).all()
    weight_by_type: dict[str, float] = {}
    total = 0.0
    for row in rows:
        w = float(row.weight)
        weight_by_type[row.evidence_type] = weight_by_type.get(row.evidence_type, 0.0) + w
        total += w
    if total <= 0:
        return {}
    return {k: round(v / total, 4) for k, v in weight_by_type.items()}


def build_career_twin_snapshot_out(db: Session, snapshot: CareerTwinSnapshot) -> CareerTwinSnapshotOut:
    """Attaches per-component `trend` (delta vs. the previous snapshot),
    `uncertainty` (1 - confidence), ripple-effect notes, and an evidence
    provenance breakdown -- all derived from already-stored data, never a
    new evidence source. See PHASE_2_EXECUTION_PLAN §"Career Twin 2.0" for
    why these are computed on read rather than stored columns."""
    from app.career_twin.ripple import compute_ripple_notes

    previous_components: dict[str, ReadinessComponent] = {}
    if snapshot.previous_snapshot_id is not None:
        previous = db.get(CareerTwinSnapshot, snapshot.previous_snapshot_id)
        if previous is not None:
            previous_components = {c.component_type: c for c in previous.components}

    ripple_by_component = compute_ripple_notes(
        db, {c.component_type: c.evidence_ids for c in snapshot.components}
    )

    milestones: list[str] = []
    components_out = []
    for component in snapshot.components:
        current_score = float(component.score) if component.score is not None else None
        previous_component = previous_components.get(component.component_type)
        previous_score = (
            float(previous_component.score)
            if previous_component is not None and previous_component.score is not None
            else None
        )
        trend = round(current_score - previous_score, 4) if current_score is not None and previous_score is not None else None
        uncertainty = round(1 - float(component.confidence), 4) if component.confidence is not None else None

        label = component.component_type.replace("_readiness", "").replace("_", " ").title()
        if (
            current_score is not None
            and current_score >= MILESTONE_SCORE_THRESHOLD
            and (previous_score is None or previous_score < MILESTONE_SCORE_THRESHOLD)
        ):
            milestones.append(f"{label} crossed {int(MILESTONE_SCORE_THRESHOLD * 100)}% readiness for the first time.")
        if (
            component.status == STATUS_SCORED
            and previous_component is not None
            and previous_component.status == STATUS_INSUFFICIENT_EVIDENCE
        ):
            milestones.append(f"{label} now has enough evidence to be scored for the first time.")

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
                evidence_diversity=component.evidence_diversity,
                is_low_sample=component.is_low_sample,
                low_sample_notice=LOW_SAMPLE_NOTICE if component.is_low_sample else None,
                stale_evidence_fraction=float(component.stale_evidence_fraction),
                is_stale_evidence=component.is_stale_evidence,
                stale_evidence_notice=(
                    f"This component's confidence is capped because "
                    f"{round(float(component.stale_evidence_fraction) * 100)}% of its evidence is 6+ months old."
                    if component.is_stale_evidence
                    else None
                ),
                ripple_notes=[
                    RippleNoteOut(target_component=n.target_component, reason=n.reason)
                    for n in ripple_by_component.get(component.component_type, [])
                ],
                provenance=_component_provenance(db, component.evidence_ids),
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
        milestones=milestones,
    )
