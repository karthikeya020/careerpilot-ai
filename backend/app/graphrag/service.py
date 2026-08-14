"""Root-cause analysis: assembles a `RootCauseResult` path from a failed
assessment question up through concept dependencies to target-role relevance
and a recommended resource. Prefers real Neo4j traversal; falls back to the
identical computation over the relational mirror when Neo4j is unreachable
*or* simply doesn't have this question/concept seeded yet (e.g. a freshly
migrated ephemeral test database that was never pointed at the seed script)
-- see PHASE_2_EXECUTION_PLAN §2.3. Every step in the returned path is
backed by a real query result; nothing here invents a relationship
(Prompt 2: "Do not fabricate graph paths").
"""

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graphrag import relational_fallback
from app.graphrag.neo4j_client import is_graph_available
from app.graphrag.repository import GraphRepository
from app.graphrag.schemas import (
    ConceptEdgeOut,
    ConceptInsightOut,
    ConceptNodeOut,
    GraphEdge,
    GraphNode,
    GraphPathStep,
    GraphSnapshot,
    GraphSource,
    RootCauseResult,
    SkillGroupOut,
    StudentGraphOverviewOut,
)
from app.models.assessment import Concept
from app.models.skill import SkillEvidence
from app.models.student import StudentProfile
from app.services import assessment_service

logger = logging.getLogger(__name__)

# ============================================================================
# Whole-graph student overview: the graph STRUCTURE (concepts + DEPENDS_ON
# edges + skill groupings) comes from Neo4j/relational_fallback exactly like
# analyze_root_cause above; the per-concept MASTERY overlay is computed here
# from the student's own SkillEvidence rows, using the same evidence-weighted
# shrinkage approach as the Career Twin's twin-v2 formula
# (app/career_twin/scoring.py) but at concept granularity. Nothing here is
# invented: a concept with no evidence is "unknown", never a guessed score
# (Constitution rule 1).
# ============================================================================

_CONCEPT_EVIDENCE_SATURATION = 2
_CONCEPT_SOURCE_DIVERSITY_TARGET = 2
_CONCEPT_NEUTRAL_PRIOR = 0.5
_STRONG_THRESHOLD = 0.72
_WEAK_THRESHOLD = 0.45
_MAX_CURATED_INSIGHTS = 6


@dataclass
class _ConceptScore:
    mastery: float | None
    confidence: float | None
    status: str
    evidence_count: int


def _score_concept(evidence: list[SkillEvidence]) -> _ConceptScore:
    if not evidence:
        return _ConceptScore(mastery=None, confidence=None, status="unknown", evidence_count=0)

    total_weight = sum(float(e.weight) for e in evidence) or 1.0
    raw_score = sum(float(e.normalized_score) * float(e.weight) for e in evidence) / total_weight
    raw_confidence = sum(float(e.confidence) * float(e.weight) for e in evidence) / total_weight
    volume_factor = min(1.0, len(evidence) / _CONCEPT_EVIDENCE_SATURATION)
    distinct_sources = len({e.source_object_type for e in evidence})
    diversity_factor = min(1.0, distinct_sources / _CONCEPT_SOURCE_DIVERSITY_TARGET)
    trust_factor = volume_factor * diversity_factor

    mastery = round(raw_score * trust_factor + _CONCEPT_NEUTRAL_PRIOR * (1 - trust_factor), 4)
    confidence = round(raw_confidence * volume_factor * diversity_factor, 4)

    if mastery >= _STRONG_THRESHOLD:
        status = "strong"
    elif mastery <= _WEAK_THRESHOLD:
        status = "weak"
    else:
        status = "developing"

    return _ConceptScore(mastery=mastery, confidence=confidence, status=status, evidence_count=len(evidence))


def _compute_depths(edges: list[dict]) -> dict[str, int]:
    """depth(x) = 0 for a concept with no prerequisites in this edge set;
    otherwise 1 + max(depth(prerequisite)). Guards defensively against a
    cycle (never expected -- concept dependencies are seeded as a DAG)."""
    dep_map: dict[str, list[str]] = {}
    all_slugs: set[str] = set()
    for e in edges:
        dep_map.setdefault(e["source"], []).append(e["target"])
        all_slugs.add(e["source"])
        all_slugs.add(e["target"])

    memo: dict[str, int] = {}

    def depth(slug: str, trail: frozenset) -> int:
        if slug in memo:
            return memo[slug]
        if slug in trail:
            return 0
        deps = dep_map.get(slug, [])
        if not deps:
            memo[slug] = 0
            return 0
        result = 1 + max(depth(dep, trail | {slug}) for dep in deps)
        memo[slug] = result
        return result

    return {slug: depth(slug, frozenset()) for slug in all_slugs}


def _build_concept_insight(
    db: Session,
    repo: GraphRepository | None,
    student_profile: StudentProfile,
    node: ConceptNodeOut,
    status_by_slug: dict[str, str],
) -> ConceptInsightOut:
    try:
        if repo is not None:
            deps = repo.concept_dependency_chain(node.slug, max_depth=2)
            blockers = repo.concepts_depending_on(node.slug, max_depth=2)
            resources = repo.resources_teaching_concept(node.slug)
        else:
            raise RuntimeError("no graph repo")
    except Exception:
        deps = relational_fallback.concept_dependency_chain(db, node.slug, max_depth=2)
        blockers = relational_fallback.concepts_depending_on(db, node.slug, max_depth=2)
        resources = relational_fallback.resources_teaching_concept(db, node.slug)

    sentences: list[str] = []
    if node.evidence_count == 0:
        sentences.append(
            f"You haven't produced any resume, assessment, or interview evidence for {node.name} yet -- "
            "this is an unverified gap, not a confirmed weakness."
        )
    else:
        mastery_pct = round((node.mastery or 0) * 100)
        confidence_pct = round((node.confidence or 0) * 100)
        sentences.append(
            f"Based on {node.evidence_count} piece{'s' if node.evidence_count != 1 else ''} of real evidence, "
            f"your mastery of {node.name} is {mastery_pct}% (confidence {confidence_pct}%)."
        )

    weak_deps = [d for d in deps if status_by_slug.get(d["slug"]) in ("weak", "unknown")]
    if node.status == "weak" and weak_deps:
        names = ", ".join(d["name"] for d in weak_deps[:2])
        sentences.append(
            f"This likely traces back to {names} -- a prerequisite you haven't mastered either. Strengthening "
            "that first will probably make this concept easier too."
        )
    elif node.status == "weak" and deps:
        names = ", ".join(d["name"] for d in deps[:2])
        sentences.append(
            f"Your prerequisites ({names}) already look solid, so this gap is specific to {node.name} itself, "
            "not something upstream."
        )

    if blockers:
        plural = "s" if len(blockers) != 1 else ""
        names = ", ".join(b["name"] for b in blockers[:3])
        sentences.append(
            f"{len(blockers)} more advanced concept{plural} build directly on this one, including {names} -- "
            "closing this gap should make those easier too."
        )

    if node.is_target_role_relevant:
        sentences.append("This concept is directly required for your target role.")

    resource = resources[0] if resources else None
    answered, total = assessment_service.concept_progress(db, student_profile.id, node.slug)

    return ConceptInsightOut(
        concept_slug=node.slug,
        concept_name=node.name,
        domain_name=node.domain_name,
        status=node.status,
        mastery=node.mastery,
        confidence=node.confidence,
        evidence_count=node.evidence_count,
        reasoning=" ".join(sentences),
        depends_on=[d["name"] for d in deps[:4]],
        blocks=[b["name"] for b in blockers[:4]],
        target_role_relevant=node.is_target_role_relevant,
        recommended_resource=(
            {"id": resource["id"], "title": resource["title"], "url": resource.get("url")} if resource else None
        ),
        practice_available=answered < total,
        questions_answered=answered,
        questions_total=total,
    )


@dataclass
class _GraphStructure:
    nodes: list[ConceptNodeOut]
    edges: list[ConceptEdgeOut]
    skills: list[SkillGroupOut]
    graph_source: GraphSource
    repo: GraphRepository | None
    target_role_title: str | None


def _compute_graph_structure(db: Session, student_profile: StudentProfile) -> _GraphStructure:
    """The cheap part: graph structure + per-concept scoring overlay. No
    reasoning paragraphs built here -- callers build those only for the
    handful of concepts they actually need (curated insights, or a single
    clicked node), not all ~40."""
    graph_source: GraphSource = "relational_fallback"
    concept_rows: list[dict] = []
    edge_rows: list[dict] = []
    role_req_rows: list[dict] = []
    repo: GraphRepository | None = None

    if is_graph_available():
        try:
            repo = GraphRepository()
            concept_rows, edge_rows = repo.all_concepts_graph()
            role_req_rows = repo.all_job_role_requirements()
            if concept_rows:
                graph_source = "neo4j"
            else:
                repo = None
        except Exception as exc:
            logger.warning("Neo4j whole-graph query failed, degrading to relational fallback: %s", exc)
            repo = None

    if not concept_rows:
        concept_rows, edge_rows = relational_fallback.all_concepts_graph(db)
        role_req_rows = relational_fallback.all_job_role_requirements(db)
        graph_source = "relational_fallback"
        repo = None

    concepts = db.scalars(select(Concept)).all()
    concept_by_slug = {c.slug: c for c in concepts}

    target_role = student_profile.primary_target_role
    target_role_title = target_role.title if target_role else None
    relevant_skill_names = (
        {r["skill_name"] for r in role_req_rows if r["title"] == target_role_title} if target_role_title else set()
    )

    evidence_rows = db.scalars(
        select(SkillEvidence).where(
            SkillEvidence.student_profile_id == student_profile.id,
            SkillEvidence.concept_id.isnot(None),
        )
    ).all()
    evidence_by_concept_id: dict[uuid.UUID, list[SkillEvidence]] = {}
    for e in evidence_rows:
        evidence_by_concept_id.setdefault(e.concept_id, []).append(e)

    depths = _compute_depths(edge_rows)

    nodes: list[ConceptNodeOut] = []
    for row in concept_rows:
        concept = concept_by_slug.get(row["slug"])
        if concept is None:
            continue
        domain = concept.domain
        score = _score_concept(evidence_by_concept_id.get(concept.id, []))
        nodes.append(
            ConceptNodeOut(
                slug=concept.slug,
                name=concept.name,
                domain_slug=domain.slug if domain else "",
                domain_name=domain.name if domain else "",
                skill_name=concept.skill.name if concept.skill else None,
                mastery=score.mastery,
                confidence=score.confidence,
                status=score.status,
                evidence_count=score.evidence_count,
                depth=depths.get(concept.slug, 0),
                is_target_role_relevant=bool(concept.skill and concept.skill.name in relevant_skill_names),
            )
        )

    node_by_slug = {n.slug: n for n in nodes}
    edges = [
        ConceptEdgeOut(source=e["source"], target=e["target"])
        for e in edge_rows
        if e["source"] in node_by_slug and e["target"] in node_by_slug
    ]

    skill_groups: dict[str, list[str]] = {}
    for n in nodes:
        if n.skill_name:
            skill_groups.setdefault(n.skill_name, []).append(n.slug)
    skills = [SkillGroupOut(name=k, concept_slugs=v) for k, v in sorted(skill_groups.items())]

    return _GraphStructure(
        nodes=nodes, edges=edges, skills=skills, graph_source=graph_source, repo=repo, target_role_title=target_role_title
    )


def get_student_graph_overview(db: Session, student_profile: StudentProfile) -> StudentGraphOverviewOut:
    structure = _compute_graph_structure(db, student_profile)
    nodes = structure.nodes
    status_by_slug = {n.slug: n.status for n in nodes}

    weak_nodes = [n for n in nodes if n.status == "weak"]
    weak_nodes.sort(key=lambda n: (not n.is_target_role_relevant, n.mastery if n.mastery is not None else 1.0))
    strong_nodes = [n for n in nodes if n.status == "strong"]
    strong_nodes.sort(key=lambda n: (n.mastery or 0), reverse=True)

    weaknesses = [
        _build_concept_insight(db, structure.repo, student_profile, n, status_by_slug)
        for n in weak_nodes[:_MAX_CURATED_INSIGHTS]
    ]
    strengths = [
        _build_concept_insight(db, structure.repo, student_profile, n, status_by_slug)
        for n in strong_nodes[:_MAX_CURATED_INSIGHTS]
    ]

    scored_masteries = [n.mastery for n in nodes if n.mastery is not None]
    scored_nodes = [n for n in nodes if n.status != "unknown"]
    overall_mastery = round(sum(scored_masteries) / len(scored_masteries), 4) if scored_masteries else None

    return StudentGraphOverviewOut(
        graph_source=structure.graph_source,
        nodes=nodes,
        edges=structure.edges,
        skills=structure.skills,
        strengths=strengths,
        weaknesses=weaknesses,
        concepts_with_evidence=len(scored_nodes),
        total_concepts=len(nodes),
        overall_mastery=overall_mastery,
        target_role_title=structure.target_role_title,
    )


def get_concept_insight(db: Session, student_profile: StudentProfile, concept_slug: str) -> ConceptInsightOut | None:
    """On-demand full detail for ANY single concept -- used when a student
    clicks a node in the graph that isn't already one of the curated
    strengths/weaknesses (e.g. a 'developing' or 'unknown' node). Only builds
    the one insight actually requested, not the whole curated set."""
    structure = _compute_graph_structure(db, student_profile)
    node = next((n for n in structure.nodes if n.slug == concept_slug), None)
    if node is None:
        return None
    status_by_slug = {n.slug: n.status for n in structure.nodes}
    return _build_concept_insight(db, structure.repo, student_profile, node, status_by_slug)


def get_resume_graph_diagnosis(db: Session, student_profile: StudentProfile, resume) -> list[ConceptInsightOut]:
    """Resume-to-graph linking: for every skill claimed on the student's
    resume that maps to a knowledge-graph Concept (via resume_service.py
    setting SkillEvidence.concept_id at parse time), returns that concept's
    real mastery/depth insight -- so a resume line like "Python" can be
    checked against actual depth evidence in the graph ("developing, missing
    Recursion and Big-O") instead of stopping at a keyword hit. Skills with
    no concept mapping are silently skipped -- there is no concept to
    diagnose, never a fabricated one (Constitution rule 1)."""
    structure = _compute_graph_structure(db, student_profile)
    status_by_slug = {n.slug: n.status for n in structure.nodes}
    resume_skill_names = {rs.skill.name for rs in resume.resume_skills}
    matching_nodes = [n for n in structure.nodes if n.skill_name and n.skill_name in resume_skill_names]
    return [
        _build_concept_insight(db, structure.repo, student_profile, node, status_by_slug)
        for node in matching_nodes
    ]


def _empty_result(graph_source) -> RootCauseResult:
    return RootCauseResult(
        graph_source=graph_source,
        concept_slug="",
        path=[],
        missing_context_warning=True,
        confidence=0.0,
    )


def analyze_root_cause(db: Session, student_profile: StudentProfile, failed_question_id: uuid.UUID) -> RootCauseResult:
    question_info = None
    graph_source: GraphSource = "relational_fallback"
    repo: GraphRepository | None = None

    if is_graph_available():
        try:
            repo = GraphRepository()
            question_info = repo.question_tests_concept(str(failed_question_id))
            if question_info:
                graph_source = "neo4j"
        except Exception as exc:
            logger.warning("Neo4j root-cause query failed, degrading to relational fallback: %s", exc)
            question_info = None
            repo = None

    if not question_info:
        question_info = relational_fallback.question_tests_concept(db, failed_question_id)
        graph_source = "relational_fallback"
        repo = None

    if not question_info:
        return _empty_result(graph_source)

    concept_slug = question_info["concept_slug"]
    concept_name = question_info["concept_name"]

    if repo is not None:
        chain = repo.concept_dependency_chain(concept_slug)
        roles = repo.job_roles_requiring_concept(concept_slug)
        resources = repo.resources_teaching_concept(concept_slug)
    else:
        chain = relational_fallback.concept_dependency_chain(db, concept_slug)
        roles = relational_fallback.job_roles_requiring_concept(db, concept_slug)
        resources = relational_fallback.resources_teaching_concept(db, concept_slug)

    student_label = student_profile.full_name or "Student"
    path: list[GraphPathStep] = [
        GraphPathStep(step_type="student", label=f"{student_label} answered a question incorrectly", node_id=str(student_profile.id)),
        GraphPathStep(
            step_type="question",
            label=f"Question tested: \"{question_info['prompt'][:90]}\"",
            node_id=str(question_info["question_id"]),
        ),
        GraphPathStep(step_type="concept", label=f"Question tests concept: {concept_name}", node_id=concept_slug),
    ]

    previous_name = concept_name
    for dep in chain:
        path.append(
            GraphPathStep(
                step_type="concept_dependency",
                label=f"{previous_name} depends on {dep['name']}",
                node_id=dep["slug"],
            )
        )
        previous_name = dep["name"]

    for role in roles:
        path.append(
            GraphPathStep(step_type="job_role", label=f"{role} requires {concept_name}", node_id=role)
        )

    for resource in resources[:1]:
        path.append(
            GraphPathStep(
                step_type="resource",
                label=f"Recommended resource \"{resource['title']}\" teaches {concept_name}",
                node_id=resource["id"],
            )
        )

    missing_context_warning = not chain and not roles and not resources
    confidence = 0.5 + (0.15 if chain else 0.0) + (0.2 if roles else 0.0) + (0.15 if resources else 0.0)
    confidence = min(confidence, 0.95)

    return RootCauseResult(
        graph_source=graph_source,
        concept_slug=concept_slug,
        path=path,
        missing_context_warning=missing_context_warning,
        confidence=round(confidence, 4),
        target_role_relevance=roles,
        recommended_resource_ids=[r["id"] for r in resources],
    )


def get_concept_neighborhood(db: Session, concept_slug: str) -> GraphSnapshot:
    if is_graph_available():
        try:
            repo = GraphRepository()
            nodes, edges = repo.concept_neighborhood(concept_slug)
            return GraphSnapshot(
                graph_source="neo4j",
                nodes=[GraphNode(id=n["id"], label=n["label"], type="concept") for n in nodes],
                edges=[GraphEdge(source=e["source"], target=e["target"], relationship=e["relationship"]) for e in edges],
            )
        except Exception as exc:
            logger.warning("Neo4j concept-neighborhood query failed, degrading to relational snapshot: %s", exc)

    chain = relational_fallback.concept_dependency_chain(db, concept_slug)
    fallback_nodes = [GraphNode(id=concept_slug, label=concept_slug, type="concept")]
    fallback_edges: list[GraphEdge] = []
    previous_slug = concept_slug
    for dep in chain:
        fallback_nodes.append(GraphNode(id=dep["slug"], label=dep["name"], type="concept"))
        fallback_edges.append(GraphEdge(source=previous_slug, target=dep["slug"], relationship="DEPENDS_ON"))
        previous_slug = dep["slug"]
    return GraphSnapshot(graph_source="relational_fallback", nodes=fallback_nodes, edges=fallback_edges)
