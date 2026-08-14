import logging
import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.scoring import recompute_twin
from app.core.config import get_settings
from app.core.errors import NotFoundError, UnprocessableError
from app.models.assessment import Concept
from app.models.audit import AuditEvent
from app.models.base import utcnow
from app.models.resume import (
    PARSING_STATUS_FAILED,
    PARSING_STATUS_PARSED,
    PARSING_STATUS_PENDING,
    SECTION_EXPERIENCE,
    SECTION_PROJECTS,
    SECTION_SKILLS,
    Resume,
    ResumeSection,
    ResumeSkill,
)
from app.models.retrieval import SOURCE_TYPE_RESUME
from app.models.skill import EVIDENCE_TYPE_PROJECT, EVIDENCE_TYPE_RESUME, SkillEvidence
from app.models.student import StudentProfile
from app.services import retrieval_service, storage
from app.services.resume_parser import detect_sections, extract_text
from app.services.skill_matching import find_skills_in_text

settings = get_settings()


class UploadLike(Protocol):
    """Structural type for anything with a filename/content_type -- satisfied
    by FastAPI's UploadFile in requests and by a plain stand-in in the seed
    script, without this module depending on FastAPI specifics."""

    filename: str | None
    content_type: str | None


ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")

# (weight, normalized_score) by section -- Skills section is an explicit
# self-labeled claim, Experience/Projects is demonstrated usage, everything
# else is a weaker incidental mention.
_SECTION_STRENGTH = {
    SECTION_PROJECTS: (0.85, 0.85),
    SECTION_EXPERIENCE: (0.85, 0.85),
    SECTION_SKILLS: (1.0, 1.0),
}
_DEFAULT_STRENGTH = (0.5, 0.6)
_KEYWORD_MATCH_CONFIDENCE = 0.7

logger = logging.getLogger(__name__)


def validate_upload(upload: UploadLike, content: bytes) -> None:
    filename = upload.filename or ""
    if not filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise UnprocessableError(
            "Unsupported file type. Upload a PDF, DOCX, or plain-text resume.",
            details={"filename": filename},
        )
    if len(content) == 0:
        raise UnprocessableError("Uploaded file is empty.")
    if len(content) > settings.max_upload_bytes:
        raise UnprocessableError(
            f"File exceeds the {settings.max_upload_bytes // (1024 * 1024)}MB upload limit.",
            details={"size_bytes": len(content)},
        )


def _section_strength(section_type: str) -> tuple[float, float]:
    return _SECTION_STRENGTH.get(section_type, _DEFAULT_STRENGTH)


def process_resume(db: Session, student_profile: StudentProfile, upload: UploadLike, content: bytes) -> Resume:
    validate_upload(upload, content)

    storage_path = storage.save(student_profile.id, upload.filename or "resume", content)
    resume = Resume(
        student_profile_id=student_profile.id,
        original_filename=upload.filename or "resume",
        storage_path=storage_path,
        content_type=upload.content_type or "application/octet-stream",
        file_size=len(content),
        parsing_status=PARSING_STATUS_PENDING,
    )
    db.add(resume)
    db.flush()

    try:
        raw_text = extract_text(content, resume.content_type, resume.original_filename)
        sections = detect_sections(raw_text)

        resume.raw_text = raw_text
        for section in sections:
            db.add(
                ResumeSection(
                    resume_id=resume.id,
                    section_type=section.section_type,
                    heading=section.heading,
                    raw_text=section.text,
                    order_index=section.order_index,
                )
            )

        # Pick the strongest section per skill if it appears more than once.
        best_by_skill: dict[uuid.UUID, tuple] = {}
        for section in sections:
            weight, normalized = _section_strength(section.section_type)
            for skill, term in find_skills_in_text(db, section.text):
                existing = best_by_skill.get(skill.id)
                if existing is None or weight > existing[1]:
                    snippet = _snippet(section.text, term)
                    best_by_skill[skill.id] = (skill, weight, normalized, section.section_type, snippet)

        concept_id_by_skill_id = {
            c.skill_id: c.id
            for c in db.scalars(
                select(Concept).where(Concept.skill_id.in_([s.id for s, *_ in best_by_skill.values()]))
            ).all()
            if c.skill_id is not None
        }

        for skill, weight, normalized, section_type, snippet in best_by_skill.values():
            db.add(
                ResumeSkill(
                    resume_id=resume.id,
                    skill_id=skill.id,
                    evidence_snippet=snippet,
                    confidence=_KEYWORD_MATCH_CONFIDENCE,
                )
            )
            evidence_type = EVIDENCE_TYPE_PROJECT if section_type == SECTION_PROJECTS else EVIDENCE_TYPE_RESUME
            db.add(
                SkillEvidence(
                    student_profile_id=student_profile.id,
                    skill_id=skill.id,
                    # Links this evidence into the knowledge-graph Concept node
                    # (when the skill maps to one) instead of a flat tag, so
                    # GraphRAG's depth/mastery reasoning can be applied to
                    # resume-sourced evidence, not just assessment attempts.
                    concept_id=concept_id_by_skill_id.get(skill.id),
                    evidence_type=evidence_type,
                    source_object_type="resume",
                    source_object_id=resume.id,
                    raw_score=normalized,
                    normalized_score=normalized,
                    weight=weight,
                    confidence=_KEYWORD_MATCH_CONFIDENCE,
                    explanation=(
                        f"'{skill.name}' detected in the resume's {section_type.replace('_', ' ')} section."
                    ),
                )
            )

        resume.parsing_status = PARSING_STATUS_PARSED
        resume.parsed_at = utcnow()
        resume.is_active = True
        _supersede_other_resumes(db, student_profile.id, keep_id=resume.id)
    except UnprocessableError as exc:
        resume.parsing_status = PARSING_STATUS_FAILED
        resume.parsing_error = exc.message
        # A failed parse produced no sections/evidence -- it must never
        # display as the student's "active" resume (the model column
        # defaults new rows to active=True before this branch runs).
        resume.is_active = False
        db.add(
            AuditEvent(
                student_profile_id=student_profile.id,
                event_type="resume_upload_failed",
                payload={"filename": resume.original_filename, "error": exc.message},
            )
        )
        db.commit()
        db.refresh(resume)
        return resume

    db.add(
        AuditEvent(
            student_profile_id=student_profile.id,
            event_type="resume_uploaded",
            payload={
                "filename": resume.original_filename,
                "sections_detected": len(sections),
                "skills_detected": len(best_by_skill),
            },
        )
    )
    db.commit()
    db.refresh(resume)

    recompute_twin(db, student_profile, reason=f"Resume '{resume.original_filename}' parsed successfully.")

    try:
        retrieval_service.index_document(
            db, source_type=SOURCE_TYPE_RESUME, source_id=resume.id, text=raw_text,
            student_profile_id=student_profile.id,
        )
    except Exception as exc:
        # Retrieval indexing is additive -- a failure here must never block
        # the resume upload itself (Constitution rule 13).
        logger.warning("Failed to index resume %s for retrieval: %s", resume.id, exc)

    return resume


def get_latest_resume(db: Session, student_profile_id: uuid.UUID) -> Resume | None:
    """Returns the student's *active* resume -- not necessarily the most
    recently uploaded row, since a student may explicitly reactivate an
    older version via `activate_resume`. Falls back to the most recently
    uploaded resume if no row is flagged active (defensive; should not
    happen given upload/activation always maintain the single-active
    invariant, but a query, not an assumption, is what proves that)."""
    active = db.scalar(
        select(Resume)
        .where(Resume.student_profile_id == student_profile_id, Resume.is_active.is_(True))
        .order_by(Resume.uploaded_at.desc())
    )
    if active is not None:
        return active
    return db.scalar(
        select(Resume)
        .where(Resume.student_profile_id == student_profile_id)
        .order_by(Resume.uploaded_at.desc())
    )


def list_resumes(db: Session, student_profile_id: uuid.UUID) -> list[Resume]:
    """Full resume history for a student, newest first -- superseded
    versions are never deleted, only marked inactive."""
    return list(
        db.scalars(
            select(Resume)
            .where(Resume.student_profile_id == student_profile_id)
            .order_by(Resume.uploaded_at.desc())
        ).all()
    )


def _supersede_other_resumes(db: Session, student_profile_id: uuid.UUID, keep_id: uuid.UUID) -> None:
    """Marks every resume for this student other than `keep_id` as inactive.
    Called after a new resume is successfully parsed, and when a student
    explicitly reactivates an older version -- maintains the invariant that
    exactly one resume is ever active per student."""
    now = utcnow()
    others = db.scalars(
        select(Resume).where(
            Resume.student_profile_id == student_profile_id,
            Resume.id != keep_id,
            Resume.is_active.is_(True),
        )
    ).all()
    for other in others:
        other.is_active = False
        other.superseded_at = now


def activate_resume(db: Session, student_profile: StudentProfile, resume_id: uuid.UUID) -> Resume:
    """Explicitly makes an older resume version active again. Recomputes the
    Career Twin immediately so the dashboard, job matches, missions, and
    every other "current profile" consumer reflect the switch without
    waiting for the next unrelated trigger (Constitution rule 13: never
    silently show a stale conclusion as current)."""
    resume = db.scalar(
        select(Resume).where(Resume.id == resume_id, Resume.student_profile_id == student_profile.id)
    )
    if resume is None:
        raise NotFoundError("Resume not found.")
    if resume.parsing_status != PARSING_STATUS_PARSED:
        raise UnprocessableError("Only a successfully parsed resume can be made active.")

    if not resume.is_active:
        resume.is_active = True
        resume.superseded_at = None
        _supersede_other_resumes(db, student_profile.id, keep_id=resume.id)
        db.add(
            AuditEvent(
                student_profile_id=student_profile.id,
                event_type="resume_activated",
                payload={"resume_id": str(resume.id), "filename": resume.original_filename},
            )
        )
        db.commit()
        db.refresh(resume)
        recompute_twin(db, student_profile, reason=f"Resume '{resume.original_filename}' was reactivated as the current resume.")

    return resume


def _snippet(text: str, term: str, radius: int = 60) -> str:
    idx = text.lower().find(term.lower())
    if idx == -1:
        return text[: radius * 2].strip()
    start = max(0, idx - radius)
    end = min(len(text), idx + len(term) + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"
