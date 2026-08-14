"""Ripple-effect cross-component notes: which other Career Twin components
would also move if a given component's evidence improved, because they
share evidence for the same skill directly, or because the skill's
knowledge-graph concept sits one hop (via ConceptDependency) from a concept
feeding another component. Purely derived from already-stored
SkillEvidence/Concept/ConceptDependency rows -- never an invented
relationship (Constitution rule 1). Computed at read time from each
component's stored evidence_ids, same "derived, not stored" pattern as
trend/uncertainty in app/career_twin/scoring.py.
"""

import uuid
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import ConceptDependency
from app.models.skill import SkillEvidence


@dataclass
class RippleNote:
    target_component: str
    reason: str


def _label(component_type: str) -> str:
    return component_type.replace("_readiness", "").replace("_", " ").title()


def compute_ripple_notes(
    db: Session, component_evidence_ids: dict[str, list[str]]
) -> dict[str, list[RippleNote]]:
    """`component_evidence_ids`: component_type -> the evidence_id strings
    stored on that component's ReadinessComponent row. Returns
    component_type -> list of RippleNote naming other components whose
    evidence overlaps, directly (same skill) or one graph hop away (a
    shared concept dependency)."""
    all_ids: set[uuid.UUID] = set()
    for ids in component_evidence_ids.values():
        all_ids.update(uuid.UUID(eid) for eid in ids)
    notes: dict[str, list[RippleNote]] = {ct: [] for ct in component_evidence_ids}
    if not all_ids:
        return notes

    evidence_rows = db.scalars(select(SkillEvidence).where(SkillEvidence.id.in_(all_ids))).all()
    evidence_by_id = {e.id: e for e in evidence_rows}

    skill_ids_by_component: dict[str, set[uuid.UUID]] = {}
    skill_names_by_component: dict[str, dict[uuid.UUID, str]] = defaultdict(dict)
    concept_ids_by_component: dict[str, set[uuid.UUID]] = {}
    for component_type, ids in component_evidence_ids.items():
        skill_set: set[uuid.UUID] = set()
        concept_set: set[uuid.UUID] = set()
        for eid in ids:
            evidence = evidence_by_id.get(uuid.UUID(eid))
            if evidence is None:
                continue
            skill_set.add(evidence.skill_id)
            skill_names_by_component[component_type][evidence.skill_id] = evidence.skill.name
            if evidence.concept_id is not None:
                concept_set.add(evidence.concept_id)
        skill_ids_by_component[component_type] = skill_set
        concept_ids_by_component[component_type] = concept_set

    all_concept_ids = {cid for concepts in concept_ids_by_component.values() for cid in concepts}
    neighbor_concepts_by_component: dict[str, set[uuid.UUID]] = {ct: set() for ct in component_evidence_ids}
    if all_concept_ids:
        dep_rows = db.scalars(
            select(ConceptDependency).where(
                ConceptDependency.concept_id.in_(all_concept_ids)
                | ConceptDependency.depends_on_id.in_(all_concept_ids)
            )
        ).all()
        for component_type, concepts in concept_ids_by_component.items():
            if not concepts:
                continue
            neighbors: set[uuid.UUID] = set()
            for dep in dep_rows:
                if dep.concept_id in concepts:
                    neighbors.add(dep.depends_on_id)
                if dep.depends_on_id in concepts:
                    neighbors.add(dep.concept_id)
            neighbor_concepts_by_component[component_type] = neighbors - concepts

    component_types = list(component_evidence_ids.keys())
    for component_a in component_types:
        for component_b in component_types:
            if component_a == component_b:
                continue
            shared_skills = skill_ids_by_component[component_a] & skill_ids_by_component[component_b]
            if shared_skills:
                names = ", ".join(sorted({skill_names_by_component[component_a][sid] for sid in shared_skills}))
                notes[component_a].append(
                    RippleNote(
                        target_component=component_b,
                        reason=(
                            f"Shares evidence for {names} with {_label(component_b)} -- "
                            f"strengthening it here should also move {_label(component_b)}."
                        ),
                    )
                )
                continue
            graph_overlap = neighbor_concepts_by_component[component_a] & concept_ids_by_component[component_b]
            if graph_overlap:
                notes[component_a].append(
                    RippleNote(
                        target_component=component_b,
                        reason=(
                            f"A prerequisite concept behind this component also feeds a concept "
                            f"{_label(component_b)} depends on."
                        ),
                    )
                )
    return notes
