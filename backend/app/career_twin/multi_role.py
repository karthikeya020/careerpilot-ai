"""Multi-role Twin view: the same evidence base, scored against several
target roles at once -- "Data Analyst: 72%, Software Engineer: 58%,
Product Manager: 41%". Role Alignment is already graph-linked to specific
job roles (app/graphrag/seed.py's JOB_ROLE_REQUIRED_SKILLS, mirrored into
Neo4j); this reuses that same role/skill-requirement data and the same
evidence-weighting function Job Match already uses
(resume_weight_by_skill), rather than inventing a second scoring system for
one target role vs. several.
"""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graphrag.seed import JOB_ROLE_REQUIRED_SKILLS
from app.models.skill import Skill
from app.services.job_description_service import resume_weight_by_skill


@dataclass
class RoleAlignment:
    role_title: str
    alignment: float
    matched_skills: list[str] = field(default_factory=list)
    missing_skills: list[str] = field(default_factory=list)


def score_multi_role_alignment(db: Session, student_profile_id: uuid.UUID) -> list[RoleAlignment]:
    weight_by_skill_id = resume_weight_by_skill(db, student_profile_id)
    all_skill_names = {name for skills in JOB_ROLE_REQUIRED_SKILLS.values() for name in skills}
    skill_by_name: dict[str, Skill] = {
        s.name: s for s in db.scalars(select(Skill).where(Skill.name.in_(all_skill_names))).all()
    }

    results: list[RoleAlignment] = []
    for role_title, required_names in JOB_ROLE_REQUIRED_SKILLS.items():
        weights: list[float] = []
        matched: list[str] = []
        missing: list[str] = []
        for name in required_names:
            skill = skill_by_name.get(name)
            weight = weight_by_skill_id.get(skill.id, 0.0) if skill else 0.0
            weights.append(weight)
            (matched if weight > 0 else missing).append(name)
        alignment = round(sum(weights) / len(weights), 4) if weights else 0.0
        results.append(
            RoleAlignment(role_title=role_title, alignment=alignment, matched_skills=matched, missing_skills=missing)
        )

    results.sort(key=lambda r: r.alignment, reverse=True)
    return results
