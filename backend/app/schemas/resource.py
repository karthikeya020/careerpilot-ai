import uuid

from pydantic import BaseModel, ConfigDict


class ResourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    provider: str
    url: str
    resource_type: str
    difficulty: int
    duration_minutes: int
    quality_score: float
    language: str
    cost: str
    source_verified: bool
    description: str


class ResourceRecommendationOut(BaseModel):
    resources: list[ResourceOut]
    reasoning_summary: str
    confidence: float
