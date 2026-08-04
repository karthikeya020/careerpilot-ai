import logging
import uuid
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.career_twin.scoring import recompute_twin
from app.core.config import get_settings
from app.core.errors import UnprocessableError
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
    except UnprocessableError as exc:
        resume.parsing_status = PARSING_STATUS_FAILED
        resume.parsing_error = exc.message
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
    return db.scalar(
        select(Resume)
        .where(Resume.student_profile_id == student_profile_id)
        .order_by(Resume.uploaded_at.desc())
    )


def _snippet(text: str, term: str, radius: int = 60) -> str:
    idx = text.lower().find(term.lower())
    if idx == -1:
        return text[: radius * 2].strip()
    start = max(0, idx - radius)
    end = min(len(text), idx + len(term) + radius)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{text[start:end].strip()}{suffix}"
