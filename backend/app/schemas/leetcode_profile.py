from pydantic import BaseModel, Field

# `status` drives which UI state the Assessment Arena widget renders. An
# unconfigured/unreachable/unknown LeetCode handle is a normal, expected
# state -- never a raw HTTP error and never an invented number
# (Constitution rule 1/4: never fabricate a stat; rule 14: every panel
# needs a real empty and error state).
LEETCODE_PROFILE_STATUSES = ("not_configured", "ok", "not_found", "unavailable")


class LeetCodeLanguageStatOut(BaseModel):
    language: str
    problems_solved: int


class LeetCodeActivityDayOut(BaseModel):
    date: str
    count: int


class LeetCodeContestOut(BaseModel):
    title: str
    start_time: str | None = None
    ranking: int | None = None
    problems_solved: int | None = None
    total_problems: int | None = None


class LeetCodeProfileOut(BaseModel):
    status: str  # one of LEETCODE_PROFILE_STATUSES

    username: str | None = None
    real_name: str | None = None
    avatar_url: str | None = None
    profile_url: str | None = None
    ranking: int | None = None

    # Solved counts vs. the total public question bank, per difficulty.
    total_solved: int = 0
    total_questions: int = 0
    easy_solved: int = 0
    easy_total: int = 0
    medium_solved: int = 0
    medium_total: int = 0
    hard_solved: int = 0
    hard_total: int = 0
    # Accepted submissions / total submissions, as a percentage. None when
    # LeetCode doesn't return submission totals for this profile.
    acceptance_rate: float | None = None

    # Streaks and activity are computed from LeetCode's own submission
    # calendar (a real per-day count), never estimated.
    current_streak_days: int = 0
    longest_streak_days: int = 0
    active_days_last_year: int = 0
    total_active_days: int = 0
    # Roughly the last 90 days of daily submission counts -- a bounded
    # window, never implying a full year of history.
    activity_heatmap: list[LeetCodeActivityDayOut] = Field(default_factory=list)

    language_stats: list[LeetCodeLanguageStatOut] = Field(default_factory=list)
    badges_count: int = 0

    # Contest activity. `contests_attended == 0` (with rating None) is the
    # honest "never competed" state.
    contests_attended: int = 0
    contest_rating: int | None = None
    contest_global_ranking: int | None = None
    contest_top_percentage: float | None = None
    recent_contests: list[LeetCodeContestOut] = Field(default_factory=list)

    last_synced_at: str | None = None
