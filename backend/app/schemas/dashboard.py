import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.audit import AuditEventOut
from app.schemas.career_twin import CareerTwinSnapshotOut, ReadinessComponentOut
from app.schemas.mission import LearningMissionOut
from app.schemas.student import TargetRoleOut


class ResumeStatusOut(BaseModel):
    uploaded: bool
    filename: str | None = None
    parsing_status: str | None = None
    parsing_error: str | None = None
    skills_detected: int = 0
    uploaded_at: datetime | None = None


class JobDescriptionStatusOut(BaseModel):
    added: bool
    title: str | None = None
    coverage: float | None = None
    matched_count: int = 0
    partial_count: int = 0
    missing_count: int = 0


class EvidenceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill_name: str
    evidence_type: str
    normalized_score: float
    confidence: float
    explanation: str
    created_at: datetime


class TwinUpdateSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    overall_score: float | None
    score_delta: float | None
    change_summary: str
    created_at: datetime


class SystemTrustOut(BaseModel):
    formula_version: str
    components_scored: int
    components_total: int
    total_evidence_count: int


class DashboardOut(BaseModel):
    student_name: str
    onboarding_completed: bool
    target_role: TargetRoleOut | None
    career_twin: CareerTwinSnapshotOut | None
    mission: LearningMissionOut | None
    priority_weakness: ReadinessComponentOut | None
    resume_status: ResumeStatusOut
    job_description_status: JobDescriptionStatusOut
    recent_evidence: list[EvidenceItemOut]
    recent_twin_updates: list[TwinUpdateSummaryOut]
    recent_audit_events: list[AuditEventOut]
    system_trust: SystemTrustOut
