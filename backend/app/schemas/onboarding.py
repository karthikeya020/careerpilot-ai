from pydantic import BaseModel, Field, field_validator


class SelfAssessedSkill(BaseModel):
    skill_name: str = Field(min_length=1, max_length=150)
    rating: float = Field(ge=0.0, le=1.0, description="Self-rated proficiency from 0 (none) to 1 (expert)")


class OnboardingRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    career_goal_description: str = Field(min_length=1, max_length=2000)
    timeline_months: int | None = Field(default=None, ge=1, le=120)
    target_role_title: str = Field(min_length=1, max_length=255)
    target_role_seniority: str = Field(default="entry_level", max_length=50)
    self_assessed_skills: list[SelfAssessedSkill] = Field(default_factory=list)
    consent_data_processing: bool = True

    @field_validator("target_role_seniority")
    @classmethod
    def normalize_seniority(cls, value: str) -> str:
        allowed = {"entry_level", "mid_level", "senior", "internship"}
        normalized = value.strip().lower().replace(" ", "_")
        if normalized not in allowed:
            raise ValueError(f"seniority must be one of {sorted(allowed)}")
        return normalized
