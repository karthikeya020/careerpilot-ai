"""Career Experiment Lab simulation engine.

Deterministic, versioned, explainable, and fully separate from any LLM call
(Prompt 3: "Do not let an LLM invent readiness gains... Allow an AI agent to
explain simulation output, but not secretly create the numeric output").
Every number this module produces is a pure function of: the student's
current Career Twin, stored evidence quantity/quality/diversity, the
concept-dependency graph, a job description's stated requirements (when one
exists), a fixed activity-effectiveness table, and an exponential
diminishing-returns curve over allocated hours. No number here is ever
computed by a model call.

Formula version `sim-v1`. See
docs/implementation/EXPERIMENT_LAB_SIMULATION.md for the full writeup.
"""

import math
import uuid
from dataclasses import dataclass, field
from statistics import mean

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Concept, ConceptDependency
from app.models.career_twin import (
    ALL_COMPONENTS,
    COMPONENT_COMMUNICATION,
    COMPONENT_TECHNICAL,
    CareerTwinSnapshot,
)
from app.models.job_description import JobDescription, JobRequirement
from app.models.skill import Skill
from app.models.student import StudentProfile, TargetRole

SIMULATION_ENGINE_VERSION = "sim-v1"

DISCLAIMER = "Personalized scenario estimate—not a guaranteed outcome or hiring prediction."

# Fixed heuristic multiplier per activity type, relative to focused practice
# problems (1.0). Not measured for any specific student -- a documented,
# calibratable assumption, not a claimed ground truth.
ACTIVITY_EFFECTIVENESS = {
    "practice_problems": 1.0,
    "mock_interview": 0.8,
    "reading": 0.5,
    "project": 1.1,
    "mixed": 0.9,
}
DEFAULT_ACTIVITY_EFFECTIVENESS = 0.7  # unrecognized activity type -> conservative default

NEUTRAL_SCORE_PRIOR = 0.5
MAX_GAIN_PER_ALLOCATION = 0.35  # component-score points, before headroom/role/history scaling
HOURS_DECAY_CONSTANT = 20.0  # hours at which raw gain reaches ~63% of its maximum (1 - e^-1)

BASELINE_DELTA_PER_SNAPSHOT = 0.03  # assumed per-snapshot improvement absent personal history
MIN_SNAPSHOTS_FOR_HISTORY = 2

REQUIRED_ROLE_IMPORTANCE = 1.0
NOT_REQUIRED_ROLE_IMPORTANCE = 0.7
DEFAULT_ROLE_IMPORTANCE = 0.6  # no job description on file -- neutral default

MIN_EVIDENCE_FOR_STABLE_CONFIDENCE = 3
MIN_SOURCE_DIVERSITY_TARGET = 2

_CATEGORY_TO_COMPONENT = {
    "technical": COMPONENT_TECHNICAL,
    "tools": COMPONENT_TECHNICAL,
    "communication": COMPONENT_COMMUNICATION,
    "soft_skill": COMPONENT_COMMUNICATION,
}


@dataclass
class AllocationInput:
    skill_name: str
    activity_type: str
    hours: float


@dataclass
class ComponentChange:
    component_type: str
    current_score: float | None
    simulated_score: float
    delta: float
    confidence: float
    uncertainty: float
    assumptions: list[str] = field(default_factory=list)
    evidence_used: list[str] = field(default_factory=list)


@dataclass
class SimulationResult:
    engine_version: str
    baseline_snapshot_id: uuid.UUID | None
    current_overall_score: float | None
    simulated_overall_score: float
    overall_score_delta: float | None
    overall_confidence: float
    overall_uncertainty: float
    component_changes: list[ComponentChange]
    assumptions: list[str]
    evidence_used: list[str]
    explanation: str
    disclaimer: str = DISCLAIMER
    # Populated after the fact by compute_sensitivity()/compute_opportunity_cost_notes()
    # below -- both re-derive from this same result rather than adding a second
    # numeric source (Constitution rule 1).
    sensitivity: list["SensitivityFactor"] = field(default_factory=list)
    waste_notes: list[str] = field(default_factory=list)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _resolve_skill(db: Session, skill_name: str) -> Skill | None:
    needle = skill_name.strip().lower()
    skills = db.scalars(select(Skill)).all()
    for skill in skills:
        if skill.name.lower() == needle:
            return skill
    for skill in skills:
        if needle in [a.lower() for a in skill.aliases]:
            return skill
    return None


def _dependents_bonus(db: Session, skill: Skill) -> float:
    """Foundational skills that other concepts depend on give a small extra
    real-world payoff (improving them helps downstream concepts too)."""
    concept = db.scalar(select(Concept).where(Concept.skill_id == skill.id))
    if concept is None:
        return 1.0
    dependents = db.scalars(select(ConceptDependency).where(ConceptDependency.depends_on_id == concept.id)).all()
    return min(1.15, 1.0 + 0.05 * len(dependents))


def _role_importance(db: Session, student_profile_id: uuid.UUID, skill: Skill) -> tuple[float, bool]:
    """Returns (importance, has_job_description). Importance is derived from
    the student's most recent job description's stated requirements when one
    exists; otherwise a documented neutral default."""
    jd = db.scalar(
        select(JobDescription)
        .where(JobDescription.student_profile_id == student_profile_id)
        .order_by(JobDescription.created_at.desc())
    )
    if jd is None:
        return DEFAULT_ROLE_IMPORTANCE, False
    requirement = db.scalar(
        select(JobRequirement).where(JobRequirement.job_description_id == jd.id, JobRequirement.skill_id == skill.id)
    )
    if requirement is None:
        return NOT_REQUIRED_ROLE_IMPORTANCE, True
    return (REQUIRED_ROLE_IMPORTANCE if requirement.is_required else NOT_REQUIRED_ROLE_IMPORTANCE), True


def _historical_response_multiplier(
    db: Session, student_profile_id: uuid.UUID, component_type: str
) -> tuple[float, bool]:
    """Returns (multiplier, has_history). Uses this student's own prior
    Career Twin snapshots for the component (real observed deltas) when at
    least two exist; otherwise a documented baseline assumption."""
    snapshots = db.scalars(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile_id)
        .order_by(CareerTwinSnapshot.version.asc())
    ).all()
    scores: list[float] = []
    for snap in snapshots:
        for component in snap.components:
            if component.component_type == component_type and component.score is not None:
                scores.append(float(component.score))
                break
    if len(scores) < MIN_SNAPSHOTS_FOR_HISTORY:
        return 1.0, False
    deltas = [scores[i] - scores[i - 1] for i in range(1, len(scores))]
    avg_delta = mean(deltas)
    if avg_delta <= 0:
        return 0.85, True
    return _clamp(avg_delta / BASELINE_DELTA_PER_SNAPSHOT, 0.7, 1.5), True


def _current_components(snapshot: CareerTwinSnapshot | None) -> dict[str, dict]:
    if snapshot is None:
        return {}
    result = {}
    for component in snapshot.components:
        result[component.component_type] = {
            "score": float(component.score) if component.score is not None else None,
            "confidence": float(component.confidence) if component.confidence is not None else None,
            "evidence_count": component.evidence_count,
            "evidence_diversity": getattr(component, "evidence_diversity", 0),
            "evidence_ids": component.evidence_ids,
        }
    return result


def simulate_scenario(
    db: Session,
    student_profile: StudentProfile,
    allocations: list[AllocationInput],
    target_role_id: uuid.UUID | None = None,
    factor_overrides: dict[str, float] | None = None,
) -> SimulationResult:
    """`factor_overrides` multiplicatively scales one of
    "activity_effectiveness" / "role_factor" / "dependents_bonus" /
    "historical_multiplier" (default 1.0 = unchanged) -- used only by
    `compute_sensitivity` below to re-run this same real computation with one
    input perturbed, never to change the formula itself."""
    overrides = factor_overrides or {}
    baseline = db.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == student_profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    current = _current_components(baseline)

    running_scores: dict[str, float] = {ct: (current.get(ct, {}).get("score") or NEUTRAL_SCORE_PRIOR) for ct in ALL_COMPONENTS}
    touched: set[str] = set()
    per_component_confidences: dict[str, list[float]] = {}
    assumptions: list[str] = [
        (
            "Activity-effectiveness weights (practice problems, mock interview, reading, project) are fixed "
            "heuristic multipliers, not measured for this specific student."
        ),
        (
            f"Gains follow an exponential diminishing-returns curve capped at +{MAX_GAIN_PER_ALLOCATION:.2f} "
            f"component-score points per allocation before role/history adjustments (half-saturation near "
            f"{HOURS_DECAY_CONSTANT:.0f} hours)."
        ),
    ]
    evidence_used: list[str] = []
    used_jd = False
    used_history = False

    if target_role_id is not None:
        role = db.get(TargetRole, target_role_id)
        if role is not None:
            assumptions.append(f"Simulated against target role '{role.title}'.")

    for allocation in allocations:
        skill = _resolve_skill(db, allocation.skill_name)
        if skill is None:
            assumptions.append(f"Skill '{allocation.skill_name}' was not recognized -- no effect simulated.")
            continue

        component_type = _CATEGORY_TO_COMPONENT.get(skill.category, COMPONENT_TECHNICAL)
        touched.add(component_type)
        base_score = running_scores[component_type]
        current_info = current.get(component_type, {})
        evidence_used.extend(current_info.get("evidence_ids", []))

        effectiveness = ACTIVITY_EFFECTIVENESS.get(allocation.activity_type, DEFAULT_ACTIVITY_EFFECTIVENESS)
        effectiveness *= overrides.get("activity_effectiveness", 1.0)
        if allocation.activity_type not in ACTIVITY_EFFECTIVENESS:
            assumptions.append(
                f"Activity type '{allocation.activity_type}' is unrecognized -- used a conservative default effectiveness."
            )

        raw_gain = MAX_GAIN_PER_ALLOCATION * (1 - math.exp(-allocation.hours / HOURS_DECAY_CONSTANT)) * effectiveness
        headroom = 1 - base_score
        headroom_factor = 0.3 + 0.7 * headroom

        role_importance, has_jd = _role_importance(db, student_profile.id, skill)
        used_jd = used_jd or has_jd
        role_factor = (0.5 + 0.5 * role_importance) * overrides.get("role_factor", 1.0)

        dependents_bonus = _dependents_bonus(db, skill) * overrides.get("dependents_bonus", 1.0)
        historical_multiplier, has_history = _historical_response_multiplier(db, student_profile.id, component_type)
        historical_multiplier *= overrides.get("historical_multiplier", 1.0)
        used_history = used_history or has_history

        gain = raw_gain * headroom_factor * role_factor * dependents_bonus * historical_multiplier
        running_scores[component_type] = _clamp(base_score + gain)

        evidence_count = current_info.get("evidence_count", 0)
        evidence_diversity = current_info.get("evidence_diversity", 0)
        evidence_confidence = min(1.0, evidence_count / MIN_EVIDENCE_FOR_STABLE_CONFIDENCE) * (
            0.4 + 0.4 * min(1.0, evidence_diversity / MIN_SOURCE_DIVERSITY_TARGET)
        )
        hours_penalty = 0.6 + 0.4 / (1 + allocation.hours / 40)
        allocation_confidence = round(_clamp(evidence_confidence * hours_penalty * (0.7 + 0.3 * role_importance), 0.05, 0.9), 4)
        per_component_confidences.setdefault(component_type, []).append(allocation_confidence)

    if used_jd:
        assumptions.append("Role importance is grounded in your most recently added job description's stated requirements.")
    else:
        assumptions.append("No job description is on file -- role importance used a neutral default weighting.")
    if used_history:
        assumptions.append("Historical learning response used this student's own prior Career Twin trend for affected components.")
    else:
        assumptions.append("Not enough Career Twin history yet -- historical learning response used a baseline assumption.")

    component_changes: list[ComponentChange] = []
    for component_type in ALL_COMPONENTS:
        if component_type not in touched:
            continue
        current_score = current.get(component_type, {}).get("score")
        simulated_score = round(running_scores[component_type], 4)
        confidences = per_component_confidences.get(component_type, [0.3])
        confidence = round(mean(confidences), 4)
        component_changes.append(
            ComponentChange(
                component_type=component_type,
                current_score=current_score,
                simulated_score=simulated_score,
                delta=round(simulated_score - (current_score if current_score is not None else NEUTRAL_SCORE_PRIOR), 4),
                confidence=confidence,
                uncertainty=round(1 - confidence, 4),
                evidence_used=current.get(component_type, {}).get("evidence_ids", []),
            )
        )

    scored_current = [c["score"] for c in current.values() if c.get("score") is not None]
    current_overall = round(mean(scored_current), 4) if scored_current else None

    simulated_component_scores = {c.component_type: c.simulated_score for c in component_changes}
    overall_components = {
        **{ct: info["score"] for ct, info in current.items() if info.get("score") is not None},
        **simulated_component_scores,
    }
    simulated_overall = round(mean(overall_components.values()), 4) if overall_components else NEUTRAL_SCORE_PRIOR
    overall_delta = round(simulated_overall - current_overall, 4) if current_overall is not None else None

    coverage = len(overall_components) / len(ALL_COMPONENTS)
    all_confidences = [c.confidence for c in component_changes] or [0.3]
    overall_confidence = round(mean(all_confidences) * coverage, 4)

    explanation = _build_explanation(component_changes, overall_delta, simulated_overall)

    return SimulationResult(
        engine_version=SIMULATION_ENGINE_VERSION,
        baseline_snapshot_id=baseline.id if baseline else None,
        current_overall_score=current_overall,
        simulated_overall_score=simulated_overall,
        overall_score_delta=overall_delta,
        overall_confidence=overall_confidence,
        overall_uncertainty=round(1 - overall_confidence, 4),
        component_changes=component_changes,
        assumptions=assumptions,
        evidence_used=list(dict.fromkeys(evidence_used)),
        explanation=explanation,
    )


def _build_explanation(component_changes: list[ComponentChange], overall_delta: float | None, simulated_overall: float) -> str:
    if not component_changes:
        return "No recognized skills were allocated hours in this scenario, so no change was simulated."
    parts = []
    for change in component_changes:
        label = change.component_type.replace("_readiness", "").replace("_", " ")
        direction = "up" if change.delta >= 0 else "down"
        parts.append(f"{label} moves {direction} by {abs(change.delta):.2f} to an estimated {change.simulated_score:.2f}")
    summary = "; ".join(parts) + "."
    if overall_delta is not None:
        direction = "up" if overall_delta >= 0 else "down"
        summary += f" Overall readiness estimate moves {direction} by {abs(overall_delta):.2f} to {simulated_overall:.2f}."
    return summary


# ---------------------------------------------------------------------------
# Sensitivity analysis: which assumption is this result most fragile to?
# ---------------------------------------------------------------------------

_SENSITIVITY_PERTURBATION = 0.2  # +/-20%
_SENSITIVITY_FACTOR_LABELS = {
    "activity_effectiveness": "assumed activity-effectiveness weight",
    "role_factor": "assumed target-role importance",
    "dependents_bonus": "assumed downstream-concept bonus",
    "historical_multiplier": "assumed personal learning-rate history",
}


@dataclass
class SensitivityFactor:
    factor: str
    label: str
    swing: float


def compute_sensitivity(
    db: Session,
    student_profile: StudentProfile,
    allocations: list[AllocationInput],
    target_role_id: uuid.UUID | None,
    baseline: SimulationResult,
) -> list[SensitivityFactor]:
    """Re-runs the real simulation with each factor scaled +/-20% in turn
    (holding the others fixed) and reports which factor moves the overall
    simulated score the most -- turning the uncertainty band already shown
    into a stated explanation of what it's most fragile to, not just a
    wider number."""
    results: list[SensitivityFactor] = []
    for factor, label in _SENSITIVITY_FACTOR_LABELS.items():
        up = simulate_scenario(db, student_profile, allocations, target_role_id, factor_overrides={factor: 1 + _SENSITIVITY_PERTURBATION})
        down = simulate_scenario(db, student_profile, allocations, target_role_id, factor_overrides={factor: 1 - _SENSITIVITY_PERTURBATION})
        swing = max(
            abs(up.simulated_overall_score - baseline.simulated_overall_score),
            abs(down.simulated_overall_score - baseline.simulated_overall_score),
        )
        results.append(SensitivityFactor(factor=factor, label=label, swing=round(swing, 4)))
    results.sort(key=lambda f: -f.swing)
    return results


# ---------------------------------------------------------------------------
# Opportunity-cost framing: name the waste explicitly.
# ---------------------------------------------------------------------------

_ALREADY_STRONG_THRESHOLD = 0.80


def compute_opportunity_cost_notes(component_changes: list[ComponentChange]) -> list[str]:
    """Flags a component whose *current* score is already at/above the
    "strong" bar but still received hours in this plan (delta > 0) --
    students consistently over-study what they're already good at; this
    names it explicitly rather than leaving it implicit in the numbers."""
    notes: list[str] = []
    for change in component_changes:
        if change.current_score is not None and change.current_score >= _ALREADY_STRONG_THRESHOLD and change.delta > 0:
            label = change.component_type.replace("_readiness", "").replace("_", " ")
            notes.append(
                f"This plan spends hours improving {label}, which is already at {change.current_score:.0%} "
                f"confidence -- consider redirecting that time to a weaker component instead."
            )
    return notes
