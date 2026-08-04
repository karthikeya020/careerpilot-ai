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

from sqlalchemy.orm import Session

from app.graphrag import relational_fallback
from app.graphrag.neo4j_client import is_graph_available
from app.graphrag.repository import GraphRepository
from app.graphrag.schemas import (
    GraphEdge,
    GraphNode,
    GraphPathStep,
    GraphSnapshot,
    GraphSource,
    RootCauseResult,
)
from app.models.student import StudentProfile

logger = logging.getLogger(__name__)


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
