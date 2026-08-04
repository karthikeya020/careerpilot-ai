"""Thin service layer over the resource catalog: listing/filtering is plain
SQL; ranked recommendation delegates to ResourceRecommendationAgent so the
same deterministic ranking logic backs both the API and the autonomous
mission-generation loop (app/services/autonomous_loop_service.py).
"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.resource_recommendation_agent import (
    ResourceRecommendationAgent,
    ResourceRecommendationInput,
)
from app.models.resource import Resource


def list_resources(db: Session, concept_slug: str | None = None, skill_name: str | None = None) -> list[Resource]:
    stmt = select(Resource)
    if concept_slug:
        from app.models.assessment import Concept

        stmt = stmt.join(Concept, Resource.concept_id == Concept.id).where(Concept.slug == concept_slug)
    if skill_name:
        from app.models.skill import Skill

        stmt = stmt.join(Skill, Resource.skill_id == Skill.id).where(Skill.name == skill_name)
    return list(db.scalars(stmt).all())


def recommend_resources(
    db: Session, concept_slug: str, available_minutes: int = 30, max_difficulty: int = 5, limit: int = 3
) -> tuple[list[Resource], str, float]:
    agent = ResourceRecommendationAgent(db)
    output, _latency = agent.safe_run(
        ResourceRecommendationInput(
            concept_slug=concept_slug, available_minutes=available_minutes, max_difficulty=max_difficulty, limit=limit
        )
    )
    found = [db.get(Resource, uuid.UUID(rid)) for rid in output.resource_ids]
    resources = [r for r in found if r is not None]
    return resources, output.reasoning_summary, output.confidence
