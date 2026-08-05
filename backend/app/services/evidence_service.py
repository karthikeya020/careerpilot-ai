"""Active-evidence filtering: the single choke point every "current profile"
consumer (Career Twin scoring, job/JD matching, CARE memory recall) must use
instead of querying `SkillEvidence` directly by `student_profile_id` alone.

Why this exists: a `SkillEvidence` row created from a resume upload
(`source_object_type == "resume"`) is permanent -- resumes are never deleted,
so history stays intact -- but only evidence sourced from the student's
*currently active* resume (`Resume.is_active`) should influence a live
result. Evidence from assessments, interviews, and job-description matches
carries no resume-version dependency and is always included. See
`app/models/resume.py` for the active-version model and
`docs/implementation/FINAL_TRUTH_FIRST_DEFECT_LEDGER.md` DEFECT-001 for the
bug this closes.
"""

import uuid

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, aliased
from sqlalchemy.sql import Select

from app.models.resume import Resume
from app.models.skill import SkillEvidence

SOURCE_TYPE_RESUME = "resume"


def active_skill_evidence_statement(student_profile_id: uuid.UUID) -> Select:
    """A `select(SkillEvidence)` statement scoped to `student_profile_id`
    that excludes resume-sourced evidence tied to a superseded resume.
    Non-resume evidence (assessment, interview, job_match, project) is
    always included, regardless of resume state. A resume-sourced row whose
    `source_object_id` does not resolve to any stored `Resume` row is also
    included (defensive default, not a real-world case for rows written by
    `resume_service.process_resume` -- it always sets a real resume id)."""
    resume_alias = aliased(Resume)
    return (
        select(SkillEvidence)
        .outerjoin(
            resume_alias,
            and_(
                SkillEvidence.source_object_type == SOURCE_TYPE_RESUME,
                SkillEvidence.source_object_id == resume_alias.id,
            ),
        )
        .where(
            SkillEvidence.student_profile_id == student_profile_id,
            or_(
                SkillEvidence.source_object_type != SOURCE_TYPE_RESUME,
                resume_alias.id.is_(None),
                resume_alias.is_active.is_(True),
            ),
        )
    )


def get_active_skill_evidence(db: Session, student_profile_id: uuid.UUID) -> list[SkillEvidence]:
    return list(db.scalars(active_skill_evidence_statement(student_profile_id)).all())
