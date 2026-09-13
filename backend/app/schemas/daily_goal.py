import uuid

from pydantic import BaseModel, Field, field_validator

DAILY_GOAL_TARGET = 5


class DailyGoalQuestionOut(BaseModel):
    question_id: uuid.UUID
    prompt: str
    domain_slug: str
    domain_name: str
    concept_slug: str
    concept_name: str
    difficulty: int
    difficulty_band: str
    # True if the student has answered at least one question in this concept
    # today -- that's what ticks a daily item off.
    done_today: bool = False


class DailyGoalOut(BaseModel):
    goal: str | None
    date: str  # today's date, ISO -- the set rotates every calendar day
    matched_domains: list[str] = []  # domain names the goal mapped to
    target_per_day: int = DAILY_GOAL_TARGET
    completed_today: int = 0
    questions: list[DailyGoalQuestionOut] = []


class SetDailyGoalRequest(BaseModel):
    # Empty string clears the goal.
    goal: str = Field(default="", max_length=200)

    @field_validator("goal")
    @classmethod
    def strip_goal(cls, value: str) -> str:
        return value.strip()
