"""Memory Agent -- responsibility: retrieve a student's recent history
(missions, evidence types, CARE activity) so other agents get continuity
instead of treating every request as a cold start. Pure DB reads, no
inference -- "memory" here means real prior records, not a vector store of
conversation turns (Phase 1/2 scope has no chat interface yet).
"""

import uuid
from typing import ClassVar

from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.base import Agent, AgentInput, AgentOutput
from app.models.mission import LearningMission
from app.models.skill import SkillEvidence

_RECENT_LIMIT = 5


class MemoryInput(AgentInput):
    student_profile_id: uuid.UUID


class MemoryOutput(AgentOutput):
    recent_mission_titles: list[str] = Field(default_factory=list)
    recent_evidence_types: list[str] = Field(default_factory=list)


class MemoryAgent(Agent[MemoryInput, MemoryOutput]):
    name = "memory"
    prompt_version = "memory-v1"
    timeout_seconds = 2.0
    allowed_tools: ClassVar[list[str]] = ["mission_history", "evidence_history"]
    output_cls = MemoryOutput

    def __init__(self, db: Session) -> None:
        self._db = db

    def run(self, agent_input: MemoryInput) -> MemoryOutput:
        missions = self._db.scalars(
            select(LearningMission)
            .where(LearningMission.student_profile_id == agent_input.student_profile_id)
            .order_by(LearningMission.created_at.desc())
            .limit(_RECENT_LIMIT)
        ).all()
        evidence = self._db.scalars(
            select(SkillEvidence)
            .where(SkillEvidence.student_profile_id == agent_input.student_profile_id)
            .order_by(SkillEvidence.created_at.desc())
            .limit(_RECENT_LIMIT)
        ).all()

        return MemoryOutput(
            confidence=1.0,
            evidence_ids=[str(e.id) for e in evidence],
            reasoning_summary=f"Found {len(missions)} recent mission(s) and {len(evidence)} recent evidence item(s).",
            inference_type="extracted_fact",
            recent_mission_titles=[m.title for m in missions],
            recent_evidence_types=[e.evidence_type for e in evidence],
        )
