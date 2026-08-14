"""Mirrors the relational Concept/ConceptDependency/Question/Resource/Skill
tables (source of truth, see PHASE_2_EXECUTION_PLAN §2.3) into Neo4j, plus a
small set of illustrative JobRole REQUIRES Skill facts so the root-cause
path can show real target-role relevance (docs/04_KNOWLEDGE_GRAPH.md's
worked example). Idempotent: every write is a MERGE, safe to re-run.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graphrag import schema as gs
from app.graphrag.neo4j_client import get_driver, is_graph_available
from app.models.assessment import Concept, ConceptDependency, Question
from app.models.resource import Resource
from app.models.skill import Skill

# Illustrative role -> required skill-name facts, matching the demo's target
# role and docs/04_KNOWLEDGE_GRAPH.md's "Data Analyst" example. Also the
# curated role set behind the Career Twin's multi-role alignment view
# (app/career_twin/multi_role.py) -- deliberately a handful of common,
# recognizable roles rather than an exhaustive taxonomy.
JOB_ROLE_REQUIRED_SKILLS = {
    "Data Analyst": ["SQL", "Python", "Data Analysis", "Pandas"],
    "Backend Engineering Intern": ["SQL", "Python", "FastAPI", "PostgreSQL"],
    "Software Engineer": ["Data Structures", "Algorithms", "System Design", "Python", "Git"],
    "Frontend Engineer": ["JavaScript", "React", "HTML", "CSS", "TypeScript"],
    "Product Manager": ["Communication", "Project Management", "Data Analysis", "Agile/Scrum"],
}


def _run_constraints(session) -> None:
    session.run("CREATE CONSTRAINT sql_concept_slug IF NOT EXISTS FOR (c:Concept) REQUIRE c.slug IS UNIQUE")
    session.run("CREATE CONSTRAINT sql_skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE")
    session.run("CREATE CONSTRAINT sql_question_id IF NOT EXISTS FOR (q:Question) REQUIRE q.id IS UNIQUE")
    session.run("CREATE CONSTRAINT sql_role_title IF NOT EXISTS FOR (r:JobRole) REQUIRE r.title IS UNIQUE")
    session.run(
        "CREATE CONSTRAINT sql_resource_id IF NOT EXISTS FOR (lr:LearningResource) REQUIRE lr.id IS UNIQUE"
    )
    session.run("CREATE CONSTRAINT sql_student_id IF NOT EXISTS FOR (st:Student) REQUIRE st.id IS UNIQUE")


def seed_graph(db: Session) -> dict:
    if not is_graph_available():
        return {"skipped": True, "reason": "neo4j unreachable"}

    driver = get_driver()
    counts = {"skills": 0, "concepts": 0, "dependencies": 0, "questions": 0, "resources": 0, "job_roles": 0}

    with driver.session() as session:
        _run_constraints(session)

        skills = db.scalars(select(Skill)).all()
        skill_id_to_name = {}
        for skill in skills:
            session.run(f"MERGE (s:{gs.LABEL_SKILL} {{name: $name}})", name=skill.name)
            skill_id_to_name[str(skill.id)] = skill.name
            counts["skills"] += 1

        concepts = db.scalars(select(Concept)).all()
        concept_id_to_slug = {}
        for concept in concepts:
            session.run(
                f"MERGE (c:{gs.LABEL_CONCEPT} {{slug: $slug}}) SET c.name = $name, c.description = $description",
                slug=concept.slug, name=concept.name, description=concept.description,
            )
            concept_id_to_slug[str(concept.id)] = concept.slug
            if concept.skill_id and str(concept.skill_id) in skill_id_to_name:
                session.run(
                    f"MATCH (s:{gs.LABEL_SKILL} {{name: $skill_name}}), (c:{gs.LABEL_CONCEPT} {{slug: $slug}}) "
                    f"MERGE (s)-[:{gs.REL_CONTAINS_CONCEPT}]->(c)",
                    skill_name=skill_id_to_name[str(concept.skill_id)], slug=concept.slug,
                )
            counts["concepts"] += 1

        deps = db.scalars(select(ConceptDependency)).all()
        for dep in deps:
            session.run(
                f"MATCH (c:{gs.LABEL_CONCEPT} {{slug: $concept_slug}}), "
                f"(d:{gs.LABEL_CONCEPT} {{slug: $depends_on_slug}}) "
                f"MERGE (c)-[:{gs.REL_DEPENDS_ON}]->(d)",
                concept_slug=concept_id_to_slug[str(dep.concept_id)],
                depends_on_slug=concept_id_to_slug[str(dep.depends_on_id)],
            )
            counts["dependencies"] += 1

        questions = db.scalars(select(Question)).all()
        for question in questions:
            concept_slug = concept_id_to_slug.get(str(question.concept_id))
            if not concept_slug:
                continue
            session.run(
                f"MERGE (q:{gs.LABEL_QUESTION} {{id: $id}}) SET q.prompt = $prompt, q.difficulty = $difficulty",
                id=str(question.id), prompt=question.prompt, difficulty=question.difficulty,
            )
            session.run(
                f"MATCH (q:{gs.LABEL_QUESTION} {{id: $id}}), (c:{gs.LABEL_CONCEPT} {{slug: $slug}}) "
                f"MERGE (q)-[:{gs.REL_TESTS}]->(c)",
                id=str(question.id), slug=concept_slug,
            )
            counts["questions"] += 1

        resources = db.scalars(select(Resource)).all()
        for resource in resources:
            concept_slug = concept_id_to_slug.get(str(resource.concept_id)) if resource.concept_id else None
            session.run(
                f"MERGE (lr:{gs.LABEL_RESOURCE} {{id: $id}}) "
                "SET lr.title = $title, lr.url = $url, lr.resource_type = $resource_type",
                id=str(resource.id), title=resource.title, url=resource.url, resource_type=resource.resource_type,
            )
            if concept_slug:
                session.run(
                    f"MATCH (lr:{gs.LABEL_RESOURCE} {{id: $id}}), (c:{gs.LABEL_CONCEPT} {{slug: $slug}}) "
                    f"MERGE (lr)-[:{gs.REL_TEACHES}]->(c)",
                    id=str(resource.id), slug=concept_slug,
                )
            counts["resources"] += 1

        for role_title, skill_names in JOB_ROLE_REQUIRED_SKILLS.items():
            session.run(f"MERGE (r:{gs.LABEL_JOB_ROLE} {{title: $title}})", title=role_title)
            for skill_name in skill_names:
                session.run(
                    f"MATCH (r:{gs.LABEL_JOB_ROLE} {{title: $title}}), (s:{gs.LABEL_SKILL} {{name: $skill_name}}) "
                    f"MERGE (r)-[:{gs.REL_REQUIRES}]->(s)",
                    title=role_title, skill_name=skill_name,
                )
            counts["job_roles"] += 1

    return counts
