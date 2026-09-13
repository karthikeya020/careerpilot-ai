import re
import uuid
from datetime import date, timedelta

from pydantic import BaseModel, ConfigDict, Field, field_validator

COLLEGE_YEAR_OPTIONS = {"1st_year", "2nd_year", "3rd_year", "4th_year", "5th_year", "graduated"}
# GitHub's own username rules: alphanumeric or single hyphens, no leading/
# trailing hyphen, max 39 chars.
_GITHUB_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
# LeetCode handles: letters, digits, underscore, hyphen and dot, up to 64
# chars. Kept permissive on purpose -- LeetCode itself is the authority, we
# only reject obviously invalid input before a lookup.
_LEETCODE_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")


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
    date_of_birth: date | None
    college_year: str | None
    branch: str | None
    github_username: str | None
    leetcode_username: str | None
    camera_consent: bool
    onboarding_completed: bool
    primary_target_role: TargetRoleOut | None
    career_goals: list[CareerGoalOut]
    target_roles: list[TargetRoleOut]


class StudentProfileUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    date_of_birth: date | None = None
    college_year: str | None = Field(default=None, max_length=50)
    branch: str | None = Field(default=None, min_length=1, max_length=150)
    github_username: str | None = Field(default=None, max_length=39)
    leetcode_username: str | None = Field(default=None, max_length=64)

    @field_validator("github_username")
    @classmethod
    def normalize_github_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if normalized.startswith(("http://", "https://")):
            normalized = normalized.rstrip("/").rsplit("/", 1)[-1]
        if not normalized:
            return None
        if not _GITHUB_USERNAME_PATTERN.match(normalized):
            raise ValueError("github_username must be a valid GitHub username")
        return normalized

    @field_validator("leetcode_username")
    @classmethod
    def normalize_leetcode_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if normalized.startswith(("http://", "https://")):
            # Accept a pasted profile URL like https://leetcode.com/u/handle/
            normalized = normalized.rstrip("/").rsplit("/", 1)[-1]
        if not normalized:
            return None
        if not _LEETCODE_USERNAME_PATTERN.match(normalized):
            raise ValueError("leetcode_username must be a valid LeetCode username")
        return normalized

    @field_validator("college_year")
    @classmethod
    def normalize_college_year(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower().replace(" ", "_")
        if normalized not in COLLEGE_YEAR_OPTIONS:
            raise ValueError(f"college_year must be one of {sorted(COLLEGE_YEAR_OPTIONS)}")
        return normalized

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date | None) -> date | None:
        if value is None:
            return None
        today = date.today()
        if value > today - timedelta(days=365 * 13):
            raise ValueError("date_of_birth must correspond to an age of at least 13 years")
        if value < today - timedelta(days=365 * 100):
            raise ValueError("date_of_birth is out of a realistic range")
        return value


class SetCameraConsentRequest(BaseModel):
    enabled: bool
