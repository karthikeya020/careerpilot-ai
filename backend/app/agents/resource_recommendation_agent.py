"""Resource Recommendation Agent -- responsibility: rank the curated
resource catalog (app/models/resource.py, seeded in the
298c98dafbbb migration) for a target concept, time budget, and difficulty
ceiling. Pure deterministic ranking over stored, source-verified rows --
Prompt 2 explicitly avoids open web scraping in the core demo, so this
agent never fetches anything external.
"""

from typing import ClassVar

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import Agent, AgentInput, AgentOutput
from app.models.assessment import Concept
from app.models.resource import Resource


class ResourceRecommendationInput(AgentInput):
    concept_slug: str
    available_minutes: int = 30
    max_difficulty: int = 5
    limit: int = 3


class ResourceRecommendationOutput(AgentOutput):
    resource_ids: list[str] = Field(default_factory=list)
    titles: list[str] = Field(default_factory=list)


class ResourceRecommendationAgent(Agent[ResourceRecommendationInput, ResourceRecommendationOutput]):
    name = "resource_recommendation"
    prompt_version = "resource-recommendation-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = ["resource_catalog"]
    output_cls = ResourceRecommendationOutput

    def __init__(self, db: Session) -> None:
        self._db = db

    def run(self, agent_input: ResourceRecommendationInput) -> ResourceRecommendationOutput:
        concept = self._db.scalar(select(Concept).where(Concept.slug == agent_input.concept_slug))
        if concept is None:
            return ResourceRecommendationOutput(
                confidence=0.0,
                evidence_ids=[],
                reasoning_summary=f"No concept found for slug '{agent_input.concept_slug}'.",
                inference_type="deterministic_calculation",
            )

        candidates = self._db.scalars(
            select(Resource).where(
                Resource.concept_id == concept.id,
                Resource.difficulty <= agent_input.max_difficulty,
                Resource.duration_minutes <= agent_input.available_minutes,
            )
        ).all()
        ranked = sorted(candidates, key=lambda r: float(r.quality_score), reverse=True)[: agent_input.limit]

        if not ranked:
            return ResourceRecommendationOutput(
                confidence=0.3,
                evidence_ids=[],
                reasoning_summary=(
                    f"No resource fit within {agent_input.available_minutes} min and difficulty "
                    f"<= {agent_input.max_difficulty} for concept '{concept.name}'."
                ),
                inference_type="deterministic_calculation",
            )

        return ResourceRecommendationOutput(
            confidence=round(min(0.6 + 0.1 * len(ranked), 0.95), 4),
            evidence_ids=[str(r.id) for r in ranked],
            reasoning_summary=f"Selected {len(ranked)} resource(s) teaching '{concept.name}', ranked by quality score.",
            inference_type="deterministic_calculation",
            resource_ids=[str(r.id) for r in ranked],
            titles=[r.title for r in ranked],
        )
