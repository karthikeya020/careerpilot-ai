"""Relational equivalents of app/graphrag/repository.py's Cypher queries,
computed from the same source-of-truth tables that seed Neo4j (see
PHASE_2_EXECUTION_PLAN §2.3). Used when `is_graph_available()` is False so
root-cause analysis degrades gracefully instead of failing (Constitution
rule 13) -- the computed path is identical in content, just labeled
`graph_source="relational_fallback"` instead of `"neo4j"`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graphrag.seed import JOB_ROLE_REQUIRED_SKILLS
from app.models.assessment import Concept, ConceptDependency, Question
from app.models.resource import Resource


def concept_dependency_chain(db: Session, slug: str, max_depth: int = 5) -> list[dict]:
    concept = db.scalar(select(Concept).where(Concept.slug == slug))
    if concept is None:
        return []

    chain: list[dict] = []
    frontier = [concept.id]
    seen = {concept.id}
    depth = 0
    while frontier and depth < max_depth:
        depth += 1
        deps = db.scalars(select(ConceptDependency).where(ConceptDependency.concept_id.in_(frontier))).all()
        next_frontier = []
        for dep in deps:
            if dep.depends_on_id in seen:
                continue
            seen.add(dep.depends_on_id)
            dep_concept = db.get(Concept, dep.depends_on_id)
            if dep_concept:
                chain.append({"slug": dep_concept.slug, "name": dep_concept.name, "depth": depth})
                next_frontier.append(dep_concept.id)
        frontier = next_frontier
    chain.sort(key=lambda item: item["depth"])
    return chain


def question_tests_concept(db: Session, question_id) -> dict | None:
    question = db.get(Question, question_id)
    if question is None:
        return None
    concept = db.get(Concept, question.concept_id)
    if concept is None:
        return None
    return {
        "question_id": str(question.id), "prompt": question.prompt,
        "concept_slug": concept.slug, "concept_name": concept.name,
    }


def job_roles_requiring_concept(db: Session, concept_slug: str) -> list[str]:
    concept = db.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is None or concept.skill_id is None:
        return []
    skill = concept.skill
    if skill is None:
        return []
    return [
        role_title
        for role_title, required_skills in JOB_ROLE_REQUIRED_SKILLS.items()
        if skill.name in required_skills
    ]


def resources_teaching_concept(db: Session, concept_slug: str) -> list[dict]:
    concept = db.scalar(select(Concept).where(Concept.slug == concept_slug))
    if concept is None:
        return []
    resources = db.scalars(select(Resource).where(Resource.concept_id == concept.id)).all()
    return [{"id": str(r.id), "title": r.title} for r in resources]
