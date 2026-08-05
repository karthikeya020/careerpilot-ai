import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.scoring import recompute_twin
from app.models.audit import AuditEvent
from app.models.job_description import REQUIREMENT_SKILL, JobDescription, JobRequirement
from app.models.retrieval import SOURCE_TYPE_JOB_DESCRIPTION
from app.models.skill import (
    EVIDENCE_TYPE_JOB_MATCH,
    EVIDENCE_TYPE_PROJECT,
    EVIDENCE_TYPE_RESUME,
    Skill,
    SkillEvidence,
)
from app.models.student import StudentProfile
from app.services import retrieval_service
from app.services.evidence_service import get_active_skill_evidence
from app.services.jd_extractor import extract_requirements

logger = logging.getLogger(__name__)

# A required skill backed only by a weak/incidental resume mention (e.g. a
# passing summary-section reference) reads as "partial" rather than "matched"
# -- mentioned, but not clearly demonstrated.
_FULL_MATCH_WEIGHT_THRESHOLD = 0.85


@dataclass
class MatchResult:
    matched_skills: list[Skill] = field(default_factory=list)
    partial_skills: list[Skill] = field(default_factory=list)
    missing_skills: list[Skill] = field(default_factory=list)
    coverage: float | None = None
    confidence: float | None = None
    explanation: str = ""


def create_job_description(
    db: Session, student_profile: StudentProfile, title: str, company: str | None, raw_text: str, source: str
) -> JobDescription:
    job_description = JobDescription(
        student_profile_id=student_profile.id,
        title=title,
        company=company,
        raw_text=raw_text,
        source=source,
    )
    db.add(job_description)
    db.flush()

    detected = extract_requirements(db, raw_text)
    for req in detected:
        db.add(
            JobRequirement(
                job_description_id=job_description.id,
                requirement_type=req.requirement_type,
                skill_id=req.skill.id if req.skill else None,
                raw_text=req.raw_text,
                is_required=req.is_required,
            )
        )

    db.add(
        AuditEvent(
            student_profile_id=student_profile.id,
            event_type="job_description_added",
            payload={"title": title, "requirements_detected": len(detected)},
        )
    )
    db.commit()
    db.refresh(job_description)

    match_result = compute_match(db, student_profile, job_description)
    _store_match_evidence(db, student_profile, job_description, match_result)

    try:
        retrieval_service.index_document(
            db, source_type=SOURCE_TYPE_JOB_DESCRIPTION, source_id=job_description.id, text=raw_text,
            student_profile_id=student_profile.id,
        )
    except Exception as exc:
        logger.warning("Failed to index job description %s for retrieval: %s", job_description.id, exc)

    return job_description


def _resume_weight_by_skill(db: Session, student_profile_id: uuid.UUID) -> dict[uuid.UUID, float]:
    # Excludes resume-sourced evidence tied to a superseded resume version
    # (app/services/evidence_service.py) -- JD/job matching must always
    # reflect the student's currently active resume, never a replaced one.
    evidence_rows = [
        row
        for row in get_active_skill_evidence(db, student_profile_id)
        if row.evidence_type in (EVIDENCE_TYPE_RESUME, EVIDENCE_TYPE_PROJECT)
    ]
    weights: dict[uuid.UUID, float] = {}
    for row in evidence_rows:
        weights[row.skill_id] = max(weights.get(row.skill_id, 0.0), float(row.weight))
    return weights


def compute_match(db: Session, student_profile: StudentProfile, job_description: JobDescription) -> MatchResult:
    """Pure computation, no DB writes -- safe to call repeatedly (e.g. on every
    GET /job-descriptions/{id}/match) without duplicating evidence."""
    required_skill_reqs = [
        req
        for req in job_description.requirements
        if req.requirement_type == REQUIREMENT_SKILL and req.is_required and req.skill_id is not None
    ]
    weight_by_skill = _resume_weight_by_skill(db, student_profile.id)

    result = MatchResult()
    seen: set[uuid.UUID] = set()
    for req in required_skill_reqs:
        skill_id = req.skill_id
        skill = req.skill
        if skill_id is None or skill is None or skill_id in seen:
            continue
        seen.add(skill_id)
        weight = weight_by_skill.get(skill_id)
        if weight is None:
            result.missing_skills.append(skill)
        elif weight >= _FULL_MATCH_WEIGHT_THRESHOLD:
            result.matched_skills.append(skill)
        else:
            result.partial_skills.append(skill)

    total = len(result.matched_skills) + len(result.partial_skills) + len(result.missing_skills)
    if total == 0:
        result.coverage = None
        result.confidence = None
        result.explanation = "No explicit skill requirements were detected in this job description."
    else:
        result.coverage = round((len(result.matched_skills) + 0.5 * len(result.partial_skills)) / total, 4)
        result.confidence = round(0.6 + 0.3 * result.coverage, 4)
        result.explanation = (
            f"{len(result.matched_skills)} of {total} required skills are clearly demonstrated in the resume, "
            f"{len(result.partial_skills)} are mentioned but weakly supported, and "
            f"{len(result.missing_skills)} were not found. Coverage is a match-quality estimate, not a hiring "
            "probability."
        )

    return result


def _store_match_evidence(
    db: Session, student_profile: StudentProfile, job_description: JobDescription, result: MatchResult
) -> None:
    """Writes SkillEvidence + audit + triggers a Twin recompute. Call exactly
    once per job description (at creation) -- not on every match read."""
    for skill in result.matched_skills + result.partial_skills:
        is_full = skill in result.matched_skills
        db.add(
            SkillEvidence(
                student_profile_id=student_profile.id,
                skill_id=skill.id,
                evidence_type=EVIDENCE_TYPE_JOB_MATCH,
                source_object_type="job_description",
                source_object_id=job_description.id,
                raw_score=1.0 if is_full else 0.5,
                normalized_score=1.0 if is_full else 0.5,
                weight=1.0,
                confidence=0.75,
                explanation=(
                    f"'{skill.name}' is required by job description '{job_description.title}' and is "
                    f"{'clearly demonstrated' if is_full else 'only weakly supported'} in the resume."
                ),
            )
        )

    db.add(
        AuditEvent(
            student_profile_id=student_profile.id,
            event_type="job_description_matched",
            payload={
                "job_description_id": str(job_description.id),
                "matched": len(result.matched_skills),
                "partial": len(result.partial_skills),
                "missing": len(result.missing_skills),
                "coverage": result.coverage,
            },
        )
    )
    db.commit()

    recompute_twin(
        db, student_profile, reason=f"Job description '{job_description.title}' matched against resume evidence."
    )


def get_match(db: Session, student_profile: StudentProfile, job_description: JobDescription) -> MatchResult:
    return compute_match(db, student_profile, job_description)


def get_job_descriptions(db: Session, student_profile_id: uuid.UUID) -> list[JobDescription]:
    return list(
        db.scalars(
            select(JobDescription)
            .where(JobDescription.student_profile_id == student_profile_id)
            .order_by(JobDescription.created_at.desc())
        ).all()
    )


def get_job_description_or_404(db: Session, student_profile_id: uuid.UUID, job_description_id: uuid.UUID):
    from app.core.errors import NotFoundError

    jd = db.scalar(
        select(JobDescription).where(
            JobDescription.id == job_description_id, JobDescription.student_profile_id == student_profile_id
        )
    )
    if jd is None:
        raise NotFoundError("Job description not found")
    return jd
