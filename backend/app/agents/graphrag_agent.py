"""GraphRAG Agent -- responsibility: wrap app/graphrag/service.py's
root-cause analysis as an agent so CARE's `graphrag_agent` route has a
uniform Agent interface, and so the traversal's path steps show up as an
AgentRun with real evidence citations in the Trust Center. The underlying
work is real Cypher (or relational-fallback) traversal -- this agent adds
no model call, only the typed wrapper. `inference_type="extracted_fact"`
because the output is literal graph facts, not a model's inference over
them.
"""

import uuid
from typing import ClassVar

from pydantic import Field
from sqlalchemy.orm import Session

from app.agents.base import Agent, AgentInput, AgentOutput
from app.graphrag.service import analyze_root_cause
from app.models.student import StudentProfile


class GraphRAGInput(AgentInput):
    failed_question_id: uuid.UUID


class GraphRAGOutput(AgentOutput):
    graph_source: str = ""
    concept_slug: str = ""
    path_summary: str = ""
    target_role_relevance: list[str] = Field(default_factory=list)
    recommended_resource_ids: list[str] = Field(default_factory=list)
    missing_context_warning: bool = True


class GraphRAGAgent(Agent[GraphRAGInput, GraphRAGOutput]):
    name = "graphrag"
    prompt_version = "graphrag-v1"
    timeout_seconds = 5.0
    allowed_tools: ClassVar[list[str]] = ["neo4j_traversal", "relational_concept_graph"]
    output_cls = GraphRAGOutput

    def __init__(self, db: Session, student_profile: StudentProfile) -> None:
        self._db = db
        self._student_profile = student_profile

    def run(self, agent_input: GraphRAGInput) -> GraphRAGOutput:
        result = analyze_root_cause(self._db, self._student_profile, agent_input.failed_question_id)
        path_summary = " -> ".join(step.label for step in result.path) or "No graph path could be resolved."
        return GraphRAGOutput(
            confidence=result.confidence,
            evidence_ids=[str(rid) for rid in result.recommended_resource_ids],
            reasoning_summary=path_summary,
            inference_type="extracted_fact",
            graph_source=result.graph_source,
            concept_slug=result.concept_slug,
            path_summary=path_summary,
            target_role_relevance=result.target_role_relevance,
            recommended_resource_ids=result.recommended_resource_ids,
            missing_context_warning=result.missing_context_warning,
        )
