import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.skill import SkillOut


class LearningMissionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description: str
    target_skill: SkillOut | None
    source_component: str
    status: str
    created_at: datetime
    completed_at: datetime | None
