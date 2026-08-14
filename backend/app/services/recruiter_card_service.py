"""Recruiter-ready evidence card: condenses the parsed resume plus its
verified evidence into a one-page, trust-scored summary -- "what a
recruiter's first six-second scan would actually notice," not a hiring
verdict. Constitution rule 5 forbids computing or displaying a probability
of being hired, so this deliberately stops at evidence completeness and
named strengths/concerns; every card carries an explicit disclaimer saying
so. Always visible to the student about their own data; a recruiter role
only ever sees it for a student who has explicitly opted in via
consent_settings.recruiter_visible (app/services/role_dashboard_service.py).
"""

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.graphrag.service import get_resume_graph_diagnosis
from app.models.resume import Resume
from app.models.skill import SkillEvidence
from app.models.student import StudentProfile
from app.services.resume_analysis_service import (
    BULLET_STRONG,
    BulletGrade,
    SelfConsistencyFlag,
    check_self_consistency,
    grade_bullets,
    score_parseability,
)

DISCLAIMER = (
    "This is an evidence-completeness signal for the student's own resume -- not a hiring recommendation, "
    "interview outcome, or placement guarantee. CareerPilot never computes or displays a probability of "
    "being hired (Constitution rule 5)."
)

_WEIGHT_PARSEABILITY = 0.25
_WEIGHT_BULLETS = 0.30
_WEIGHT_SELF_CONSISTENCY = 0.20
_WEIGHT_GRAPH_DEPTH = 0.25


@dataclass
class RecruiterCard:
    has_resume: bool
    trust_score: float | None
    strengths: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    verified_skill_count: int = 0
    total_skill_count: int = 0
    parseability_score: float | None = None
    bullet_strong_ratio: float | None = None
    disclaimer: str = DISCLAIMER


def _bullet_component(grades: list[BulletGrade]) -> tuple[float | None, list[str], list[str]]:
    if not grades:
        return None, [], []
    strong = [g for g in grades if g.strength == BULLET_STRONG]
    weak = [g for g in grades if g.strength != BULLET_STRONG and g.fix_suggestion]
    ratio = len(strong) / len(grades)
    strengths = [f"{len(strong)} of {len(grades)} experience/project bullets read as strong, evidence-backed claims."] if strong else []
    concerns = [f"Weak bullet: \"{g.text[:90]}\" -- {g.fix_suggestion}" for g in weak[:3]]
    return ratio, strengths, concerns


def _self_consistency_component(flags: list[SelfConsistencyFlag], total_skills: int) -> tuple[float | None, list[str]]:
    if total_skills == 0:
        return None, []
    ratio = 1 - (len(flags) / total_skills)
    concerns = [f.message for f in flags[:3]]
    return ratio, concerns


def build_recruiter_card(db: Session, student_profile: StudentProfile, resume: Resume | None) -> RecruiterCard:
    if resume is None or resume.parsing_status != "parsed":
        return RecruiterCard(has_resume=False, trust_score=None)

    parseability = score_parseability(resume)
    bullet_grades = grade_bullets(resume)
    consistency_flags = check_self_consistency(db, resume)
    graph_insights = get_resume_graph_diagnosis(db, student_profile, resume)

    strengths: list[str] = []
    concerns: list[str] = list(parseability.warnings)

    bullet_ratio, bullet_strengths, bullet_concerns = _bullet_component(bullet_grades)
    strengths.extend(bullet_strengths)
    concerns.extend(bullet_concerns)

    total_skills = len(resume.resume_skills)
    consistency_ratio, consistency_concerns = _self_consistency_component(consistency_flags, total_skills)
    concerns.extend(consistency_concerns)

    evidenced_skill_ids = set(
        db.scalars(
            select(SkillEvidence.skill_id).where(SkillEvidence.student_profile_id == student_profile.id)
        ).all()
    )
    verified_skill_count = sum(1 for rs in resume.resume_skills if rs.skill_id in evidenced_skill_ids)
    if verified_skill_count:
        strengths.append(
            f"{verified_skill_count} of {total_skills} listed skills have at least one traceable evidence source."
        )

    graph_depth_component = None
    weak_or_unknown_relevant = [
        n for n in graph_insights if n.status in ("weak", "unknown") and n.target_role_relevant
    ]
    if graph_insights:
        graph_depth_component = sum(1 for n in graph_insights if n.status in ("strong", "developing")) / len(graph_insights)
        for node in weak_or_unknown_relevant[:2]:
            concerns.append(
                f"\"{node.concept_name}\" appears on the resume but the knowledge graph shows little depth "
                f"evidence for it, and it's directly relevant to the target role."
            )

    components: list[tuple[float, float]] = [(parseability.score, _WEIGHT_PARSEABILITY)]
    if bullet_ratio is not None:
        components.append((bullet_ratio, _WEIGHT_BULLETS))
    if consistency_ratio is not None:
        components.append((consistency_ratio, _WEIGHT_SELF_CONSISTENCY))
    if graph_depth_component is not None:
        components.append((graph_depth_component, _WEIGHT_GRAPH_DEPTH))

    total_weight = sum(w for _, w in components) or 1.0
    trust_score = round(sum(v * w for v, w in components) / total_weight, 4)

    if not concerns:
        concerns.append("No significant evidence gaps detected in this pass.")

    return RecruiterCard(
        has_resume=True,
        trust_score=trust_score,
        strengths=strengths,
        concerns=concerns,
        verified_skill_count=verified_skill_count,
        total_skill_count=total_skills,
        parseability_score=parseability.score,
        bullet_strong_ratio=bullet_ratio,
        disclaimer=DISCLAIMER,
    )
