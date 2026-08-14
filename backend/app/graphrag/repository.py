"""Real Cypher queries against Neo4j. Every method here either returns data
that was actually read from the graph, or raises -- callers (app/graphrag/
service.py) are responsible for checking `is_graph_available()` first and
falling back to the relational mirror otherwise. This file never invents a
path; if a query returns nothing, the caller sees an empty list.
"""

from app.graphrag import schema as gs
from app.graphrag.neo4j_client import get_driver


class GraphRepository:
    def __init__(self) -> None:
        self._driver = get_driver()

    def concept(self, slug: str) -> dict | None:
        with self._driver.session() as session:
            record = session.run(
                f"MATCH (c:{gs.LABEL_CONCEPT} {{slug: $slug}}) RETURN c.slug AS slug, c.name AS name", slug=slug
            ).single()
            return dict(record) if record else None

    def concept_dependency_chain(self, slug: str, max_depth: int = 5) -> list[dict]:
        """Nearest-first list of concepts `slug` (transitively) DEPENDS_ON."""
        with self._driver.session() as session:
            result = session.run(
                f"MATCH (c:{gs.LABEL_CONCEPT} {{slug: $slug}})-[:{gs.REL_DEPENDS_ON}*1..{max_depth}]->(d:{gs.LABEL_CONCEPT}) "
                "WITH DISTINCT d, min(size([(c)-[:DEPENDS_ON*]->(d) | 1])) AS depth "
                "RETURN d.slug AS slug, d.name AS name, depth ORDER BY depth ASC",
                slug=slug,
            )
            return [dict(record) for record in result]

    def question_tests_concept(self, question_id: str) -> dict | None:
        with self._driver.session() as session:
            record = session.run(
                f"MATCH (q:{gs.LABEL_QUESTION} {{id: $id}})-[:{gs.REL_TESTS}]->(c:{gs.LABEL_CONCEPT}) "
                "RETURN q.id AS question_id, q.prompt AS prompt, c.slug AS concept_slug, c.name AS concept_name",
                id=question_id,
            ).single()
            return dict(record) if record else None

    def job_roles_requiring_concept(self, concept_slug: str) -> list[str]:
        with self._driver.session() as session:
            result = session.run(
                f"MATCH (r:{gs.LABEL_JOB_ROLE})-[:{gs.REL_REQUIRES}]->(s:{gs.LABEL_SKILL})"
                f"-[:{gs.REL_CONTAINS_CONCEPT}]->(c:{gs.LABEL_CONCEPT} {{slug: $slug}}) "
                "RETURN DISTINCT r.title AS title",
                slug=concept_slug,
            )
            return [record["title"] for record in result]

    def resources_teaching_concept(self, concept_slug: str) -> list[dict]:
        with self._driver.session() as session:
            result = session.run(
                f"MATCH (lr:{gs.LABEL_RESOURCE})-[:{gs.REL_TEACHES}]->(c:{gs.LABEL_CONCEPT} {{slug: $slug}}) "
                "RETURN lr.id AS id, lr.title AS title, lr.url AS url",
                slug=concept_slug,
            )
            return [dict(record) for record in result]

    def all_concepts_graph(self) -> tuple[list[dict], list[dict]]:
        """Every Concept node (with its containing Skill, if any) and every
        DEPENDS_ON edge in the whole graph -- the full knowledge graph, not a
        single concept's neighborhood."""
        with self._driver.session() as session:
            node_result = session.run(
                f"MATCH (c:{gs.LABEL_CONCEPT}) "
                f"OPTIONAL MATCH (s:{gs.LABEL_SKILL})-[:{gs.REL_CONTAINS_CONCEPT}]->(c) "
                "RETURN c.slug AS slug, c.name AS name, s.name AS skill_name"
            )
            nodes = [dict(record) for record in node_result]
            edge_result = session.run(
                f"MATCH (c:{gs.LABEL_CONCEPT})-[:{gs.REL_DEPENDS_ON}]->(d:{gs.LABEL_CONCEPT}) "
                "RETURN c.slug AS source, d.slug AS target"
            )
            edges = [dict(record) for record in edge_result]
            return nodes, edges

    def concepts_depending_on(self, slug: str, max_depth: int = 3) -> list[dict]:
        """Reverse of concept_dependency_chain: concepts that (transitively)
        depend ON `slug` -- i.e. what this concept unlocks/blocks."""
        with self._driver.session() as session:
            result = session.run(
                f"MATCH (c:{gs.LABEL_CONCEPT})-[:{gs.REL_DEPENDS_ON}*1..{max_depth}]->"
                f"(target:{gs.LABEL_CONCEPT} {{slug: $slug}}) "
                "WITH DISTINCT c, min(size([(c)-[:DEPENDS_ON*]->(target) | 1])) AS depth "
                "RETURN c.slug AS slug, c.name AS name, depth ORDER BY depth ASC",
                slug=slug,
            )
            return [dict(record) for record in result]

    def all_job_role_requirements(self) -> list[dict]:
        with self._driver.session() as session:
            result = session.run(
                f"MATCH (r:{gs.LABEL_JOB_ROLE})-[:{gs.REL_REQUIRES}]->(s:{gs.LABEL_SKILL}) "
                "RETURN r.title AS title, s.name AS skill_name"
            )
            return [dict(record) for record in result]

    def concept_neighborhood(self, slug: str, max_depth: int = 3) -> tuple[list[dict], list[dict]]:
        """Nodes + edges around `slug` for the graph-visualization API."""
        with self._driver.session() as session:
            result = session.run(
                f"MATCH path = (c:{gs.LABEL_CONCEPT} {{slug: $slug}})-[:{gs.REL_DEPENDS_ON}*0..{max_depth}]->(d:{gs.LABEL_CONCEPT}) "
                "UNWIND relationships(path) AS rel "
                "RETURN DISTINCT startNode(rel).slug AS source_slug, startNode(rel).name AS source_name, "
                "endNode(rel).slug AS target_slug, endNode(rel).name AS target_name, type(rel) AS relationship",
                slug=slug,
            )
            nodes: dict[str, dict] = {}
            edges: list[dict] = []
            for record in result:
                nodes[record["source_slug"]] = {"id": record["source_slug"], "label": record["source_name"]}
                nodes[record["target_slug"]] = {"id": record["target_slug"], "label": record["target_name"]}
                edges.append(
                    {"source": record["source_slug"], "target": record["target_slug"], "relationship": record["relationship"]}
                )
            if not nodes:
                seed = self.concept(slug)
                if seed:
                    nodes[seed["slug"]] = {"id": seed["slug"], "label": seed["name"]}
            return list(nodes.values()), edges
