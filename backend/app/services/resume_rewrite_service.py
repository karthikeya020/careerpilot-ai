"""Orchestrates evidence-only rewrite suggestions for a student's weak or
missing skills, pairing naturally with Job Match's gap plan. Invokes
ResumeRewriteAgent directly rather than through the full CARE routing engine
-- a bullet rewrite is presentation-only, not a Career Twin score, so it
doesn't need a RoutingFactors/DecisionTrace audit trail the way scoring
decisions do (Constitution rule 3 scopes that requirement to Career Twin
writes specifically); the agent's typed confidence/evidence_ids/inference_type
output still applies (Constitution rule 4)."""

import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.resume_rewrite_agent import ResumeRewriteAgent, ResumeRewriteInput
from app.models.resume import Resume
from app.models.skill import Skill, SkillEvidence
from app.models.student import StudentProfile
from app.services.job_catalog_service import simulate_job_gap


@dataclass
class RewriteSuggestion:
    skill_name: str
    status: str
    has_sufficient_evidence: bool
    rewritten_bullet: str | None
    note: str


def _evidence_snippets_for_skill(db: Session, student_profile_id: uuid.UUID, resume: Resume | None, skill: Skill) -> list[str]:
    snippets: list[str] = []
    if resume is not None:
        for rs in resume.resume_skills:
            if rs.skill_id == skill.id and rs.evidence_snippet:
                snippets.append(rs.evidence_snippet)
    other_evidence = db.scalars(
        select(SkillEvidence).where(
            SkillEvidence.student_profile_id == student_profile_id,
            SkillEvidence.skill_id == skill.id,
        )
    ).all()
    for e in other_evidence:
        if e.explanation and e.explanation not in snippets:
            snippets.append(e.explanation)
    return snippets


def suggest_rewrites_for_gap(
    db: Session, student_profile: StudentProfile, resume: Resume | None, listing_id: uuid.UUID
) -> list[RewriteSuggestion]:
    """Evidence-only rewrite suggestions scoped to a specific tracked Job
    Match dream job's gap plan -- one suggestion per missing/partial skill,
    each independently allowed to come back "insufficient evidence" (never a
    fabricated bullet for a skill the student hasn't actually demonstrated)."""
    plan = simulate_job_gap(db, student_profile, listing_id)
    agent = ResumeRewriteAgent()
    suggestions: list[RewriteSuggestion] = []
    for item in plan.items:
        skill = db.scalar(select(Skill).where(Skill.name == item.skill_name))
        if skill is None:
            continue
        snippets = _evidence_snippets_for_skill(db, student_profile.id, resume, skill)
        output, _latency = agent.safe_run(
            ResumeRewriteInput(skill_name=skill.name, evidence_snippets=snippets, evidence_ids=[])
        )
        suggestions.append(
            RewriteSuggestion(
                skill_name=skill.name,
                status=item.status,
                has_sufficient_evidence=output.has_sufficient_evidence,
                rewritten_bullet=output.rewritten_bullet,
                note=output.note,
            )
        )
    return suggestions
