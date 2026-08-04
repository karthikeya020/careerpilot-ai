from pydantic import BaseModel


class CohortSkillGapOut(BaseModel):
    component_type: str
    average_score: float | None
    scored_student_count: int


class StudentNeedingSupportOut(BaseModel):
    student_profile_id: str
    full_name: str
    flagged_decision_count: int


class FacultyDashboardOut(BaseModel):
    total_students: int
    cohort_skill_gaps: list[CohortSkillGapOut]
    mission_completion_rate: float | None
    assessment_completion_rate: float | None
    average_readiness_trend: float | None
    students_needing_support: list[StudentNeedingSupportOut]


class ReadinessBucketOut(BaseModel):
    range_start: int
    range_end: int
    student_count: int


class PlacementDashboardOut(BaseModel):
    student_count_with_snapshot: int
    readiness_distribution: list[ReadinessBucketOut]
    role_alignment_average: float | None
    common_skill_gaps: list[CohortSkillGapOut]
    program_effectiveness_average_delta: float | None
    disclaimer: str


class CandidateComponentOut(BaseModel):
    component_type: str
    score: float | None
    confidence: float | None
    status: str


class RecruiterCandidateOut(BaseModel):
    student_profile_id: str
    full_name: str
    target_role: str | None
    overall_score: float | None
    overall_confidence: float | None
    components: list[CandidateComponentOut]
    requires_human_review: bool
    consent_status: str


class ServiceHealthOut(BaseModel):
    database: bool
    redis: bool
    neo4j: bool


class CareExecutionStatsOut(BaseModel):
    total_executions: int
    route_frequency: dict[str, int]
    average_confidence: float | None
    average_latency_ms: float | None
    average_cost_usd: float | None
    human_review_rate: float | None


class RecentAuditEventOut(BaseModel):
    id: str
    event_type: str
    created_at: str


class AdminDashboardOut(BaseModel):
    service_health: ServiceHealthOut
    users_by_role: dict[str, int]
    total_users: int
    care_execution_stats: CareExecutionStatsOut
    recent_audit_events: list[RecentAuditEventOut]


class SetRecruiterVisibilityRequest(BaseModel):
    visible: bool
