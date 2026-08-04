from typing import Literal

from pydantic import BaseModel, Field

GraphSource = Literal["neo4j", "relational_fallback"]
PathStepType = Literal[
    "student", "question", "concept", "concept_dependency", "job_role", "resource", "inference"
]


class GraphPathStep(BaseModel):
    step_type: PathStepType
    label: str
    node_id: str | None = None
    # True only for a step that is not a direct graph edge/node -- e.g. a
    # synthesized natural-language connector. Every non-inference step must
    # correspond to a real node/relationship that was actually queried
    # (Prompt 2: "Do not fabricate graph paths").
    is_inference: bool = False


class RootCauseResult(BaseModel):
    graph_source: GraphSource
    concept_slug: str
    path: list[GraphPathStep]
    missing_context_warning: bool
    confidence: float
    target_role_relevance: list[str] = Field(default_factory=list)
    recommended_resource_ids: list[str] = Field(default_factory=list)


class GraphNode(BaseModel):
    id: str
    label: str
    type: PathStepType


class GraphEdge(BaseModel):
    source: str
    target: str
    relationship: str


class GraphSnapshot(BaseModel):
    graph_source: GraphSource
    nodes: list[GraphNode]
    edges: list[GraphEdge]
