from pydantic import BaseModel, Field, field_validator

MAX_CODE_CHARS = 20000


class LeetCodeCompletionOut(BaseModel):
    slug: str
    title: str
    difficulty: str
    concept_slug: str | None = None
    domain_slug: str | None = None
    completed_at: str
    analyzed_at: str | None = None
    has_analysis: bool = False


class CodeReviewOut(BaseModel):
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    time_complexity: str = ""
    space_complexity: str = ""
    complexity_explanation: str = ""
    how_to_think: str = ""
    ai_generated: bool = False


class SimilarProblemOut(BaseModel):
    slug: str
    title: str
    difficulty: str
    url: str


class LeetCodeAnalysisOut(BaseModel):
    slug: str
    title: str
    # Shown immediately in the pop-up, before any code is pasted.
    how_to_think: str
    similar_problems: list[SimilarProblemOut] = Field(default_factory=list)
    # Present only once the student has run "Explain".
    language: str | None = None
    code: str | None = None
    review: CodeReviewOut | None = None
    analyzed_at: str | None = None


class MarkCompleteRequest(BaseModel):
    slug: str = Field(min_length=1, max_length=160)
    title: str = Field(min_length=1, max_length=200)
    difficulty: str = Field(default="", max_length=10)
    concept_slug: str | None = Field(default=None, max_length=80)
    domain_slug: str | None = Field(default=None, max_length=50)


class AnalyzeCodeRequest(BaseModel):
    code: str = Field(min_length=1)
    language: str | None = Field(default=None, max_length=30)

    @field_validator("code")
    @classmethod
    def cap_code(cls, value: str) -> str:
        if len(value) > MAX_CODE_CHARS:
            raise ValueError(f"code must be at most {MAX_CODE_CHARS} characters")
        return value
