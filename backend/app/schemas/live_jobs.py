from pydantic import BaseModel, Field

# importance of a skill to a role, inferred from where it sits in the JD:
#   core     -> in the hard requirements / repeated / "must have"
#   strong   -> named in the body, expected day-to-day
#   familiar -> only in "nice to have" / "bonus"
LIVE_JOB_SKILL_IMPORTANCE = ("core", "strong", "familiar")


class LiveJobSkillOut(BaseModel):
    name: str
    importance: str  # one of LIVE_JOB_SKILL_IMPORTANCE


class LiveJobOut(BaseModel):
    id: str
    company: str
    title: str
    location: str
    remote: bool = False
    url: str
    sector: str
    source: str  # "greenhouse" | "lever" | "catalog"
    posted_at: str | None = None
    team: str | None = None
    summary: str
    description: str
    responsibilities: list[str] = Field(default_factory=list)
    requirements: list[str] = Field(default_factory=list)
    skills: list[LiveJobSkillOut] = Field(default_factory=list)
    comp_note: str | None = None
    # True when pulled live from a company board; False for the curated fallback.
    is_live: bool = True
    # Title looks like an internship / co-op / trainee posting.
    is_internship: bool = False


class LiveJobFeedOut(BaseModel):
    jobs: list[LiveJobOut]
    # Endless reel: keep requesting with this cursor; the feed wraps at the end.
    next_cursor: int
    total: int
    live: bool  # did any live board contribute, or is this the curated fallback?


class LiveJobSearchOut(BaseModel):
    jobs: list[LiveJobOut]
    total: int
    live: bool


class TrackLiveJobRequest(BaseModel):
    id: str = Field(min_length=3, max_length=200)


class SkillMatchOut(BaseModel):
    """Resume-evidence match for an arbitrary skill list (a live posting's
    extracted skills). Same scoring as catalog readiness."""

    readiness: float | None = None
    matched: list[str] = Field(default_factory=list)
    partial: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)
