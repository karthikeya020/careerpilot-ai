from pydantic import BaseModel


class VersionInfoOut(BaseModel):
    care_policy_version: str
    career_twin_formula_version: str
    simulation_engine_version: str
    agent_prompt_versions: dict[str, str]


class HumanReviewStatusOut(BaseModel):
    pending_count: int


class ResponsibleAIOverviewOut(BaseModel):
    evaluates: list[str]
    does_not_evaluate: list[str]
    versions: VersionInfoOut
    human_review: HumanReviewStatusOut
    evidence_provenance: dict[str, int]
    current_career_twin_confidence: float | None
    consent: dict
    stored_interview_audio_count: int
    non_claims: list[str]


class AudioDeletionResultOut(BaseModel):
    deleted_count: int
