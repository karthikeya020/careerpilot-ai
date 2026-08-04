import uuid

from pydantic import BaseModel, ConfigDict


class TargetRoleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    seniority: str
    is_primary: bool


class CareerGoalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    timeline_months: int | None
    is_active: bool


class StudentProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    onboarding_completed: bool
    primary_target_role: TargetRoleOut | None
    career_goals: list[CareerGoalOut]
    target_roles: list[TargetRoleOut]
