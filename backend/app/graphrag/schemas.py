import uuid
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


ConceptStatus = Literal["strong", "developing", "weak", "unknown"]


class ConceptNodeOut(BaseModel):
    slug: str
    name: str
    domain_slug: str
    domain_name: str
    skill_name: str | None = None
    mastery: float | None = None
    confidence: float | None = None
    status: ConceptStatus
    evidence_count: int
    depth: int
    is_target_role_relevant: bool = False


class ConceptEdgeOut(BaseModel):
    source: str
    target: str


class SkillGroupOut(BaseModel):
    name: str
    concept_slugs: list[str]


class ConceptInsightOut(BaseModel):
    concept_slug: str
    concept_name: str
    domain_name: str
    status: ConceptStatus
    mastery: float | None
    confidence: float | None
    evidence_count: int
    reasoning: str
    depends_on: list[str]
    blocks: list[str]
    target_role_relevant: bool
    recommended_resource: dict | None = None
    practice_available: bool
    questions_answered: int
    questions_total: int


class StudentGraphOverviewOut(BaseModel):
    graph_source: GraphSource
    nodes: list[ConceptNodeOut]
    edges: list[ConceptEdgeOut]
    skills: list[SkillGroupOut]
    strengths: list[ConceptInsightOut]
    weaknesses: list[ConceptInsightOut]
    concepts_with_evidence: int
    total_concepts: int
    overall_mastery: float | None
    target_role_title: str | None


# ---- Embedded practice (answer questions for a weak concept without ever
# leaving the GraphRAG page) ----


class PracticeQuestionOut(BaseModel):
    id: uuid.UUID
    question_type: str
    prompt: str
    options: list | None
    difficulty: int
    difficulty_band: str


class PracticeProgressOut(BaseModel):
    attempt_id: uuid.UUID
    concept_slug: str
    is_correct: bool | None = None
    score: float | None = None
    explanation: str = ""
    next_question: PracticeQuestionOut | None
    is_complete: bool
    answered_in_concept: int
    total_in_concept: int


class PracticeAnswerRequest(BaseModel):
    question_id: uuid.UUID
    response_payload: dict
    time_spent_seconds: int | None = None
