from pydantic import BaseModel, Field

GITHUB_PROFILE_STATUSES = ("not_configured", "ok", "not_found", "unavailable")


class GithubRepoOut(BaseModel):
    name: str
    html_url: str
    language: str | None = None
    stargazers_count: int = 0
    pushed_at: str | None = None


class GithubActivityDayOut(BaseModel):
    date: str
    count: int


class GithubProfileOut(BaseModel):
    """`status` drives which UI state the widget renders -- never a raw
    HTTP error, since an unconfigured/unreachable GitHub profile is a normal,
    expected state (Constitution rule 14: every panel needs a real empty and
    error state), not a fault in the request itself."""

    status: str  # one of GITHUB_PROFILE_STATUSES
    username: str | None = None
    name: str | None = None
    bio: str | None = None
    avatar_url: str | None = None
    html_url: str | None = None
    public_repos: int = 0
    followers: int = 0
    account_created_at: str | None = None
    # Repo count per primary language, non-fork repos only -- a count, not
    # byte-weighted, so the UI never overstates precision (Constitution rule 4).
    language_breakdown: dict[str, int] = Field(default_factory=dict)
    # Public events from roughly the last 90 days -- GitHub's real retention
    # window for the public events API. Never implies a full year of history.
    activity_heatmap: list[GithubActivityDayOut] = Field(default_factory=list)
    top_repos: list[GithubRepoOut] = Field(default_factory=list)
    last_synced_at: str | None = None
