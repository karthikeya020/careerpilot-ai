from pydantic import BaseModel, Field

# "assessment" -> groups are keyed to concepts the student measurably struggled
#   with (accuracy below threshold in their own stored responses).
# "profile"    -> no assessment history yet, so recommendations fall back to the
#   student's resume-matched / all domains.
# "no_weaknesses" -> the student has assessment history but nothing below the
#   weakness threshold; a few stretch problems are offered from their
#   lowest-scoring area, clearly labelled as such.
LEETCODE_RECOMMENDATION_SOURCES = ("assessment", "profile", "no_weaknesses")


class LeetCodeRecommendedProblemOut(BaseModel):
    slug: str
    title: str
    difficulty: str  # "Easy" | "Medium" | "Hard"
    url: str


class WeaknessGroupOut(BaseModel):
    """One weak area and the problems that target it. `accuracy` / `answered`
    are real reads of the student's assessment responses -- null on the
    profile fallback path where there's nothing measured yet."""

    concept_slug: str | None = None
    concept_name: str
    domain_slug: str
    domain_name: str
    accuracy: float | None = None
    answered: int = 0
    focus: str = ""
    problems: list[LeetCodeRecommendedProblemOut] = Field(default_factory=list)


class LeetCodeRecommendationsOut(BaseModel):
    source: str  # one of LEETCODE_RECOMMENDATION_SOURCES
    summary: str
    weakness_threshold: float
    groups: list[WeaknessGroupOut] = Field(default_factory=list)
    disclaimer: str = (
        "Problem picks are from a curated static list mapped to each concept -- "
        "verify any slug at leetcode.com/problems/<slug>."
    )
