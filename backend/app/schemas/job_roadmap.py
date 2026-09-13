from pydantic import BaseModel, Field

ROADMAP_DIFFICULTY = ("brutal", "hard", "achievable")


class RoadmapAction(BaseModel):
    text: str
    # In-app route (/assessment, /interview, /graphrag) or an external URL.
    link: str | None = None


class RoadmapPhase(BaseModel):
    title: str
    weeks: str  # e.g. "Weeks 1-4"
    why: str
    actions: list[RoadmapAction] = Field(default_factory=list)
    milestone: str


class JobRoadmapOut(BaseModel):
    company: str
    title: str
    sector: str
    seniority: str
    difficulty: str  # one of ROADMAP_DIFFICULTY
    # A blunt, no-sugar-coating read of the hiring bar.
    bar: str
    total_weeks: int
    summary: str
    skills_focus: list[str] = Field(default_factory=list)
    phases: list[RoadmapPhase] = Field(default_factory=list)
