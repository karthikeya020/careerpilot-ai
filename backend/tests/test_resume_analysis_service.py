"""Bullet-strength grading, the self-consistency check, and the
parseability/ATS score -- all deterministic, computed fresh from a real
parsed Resume row (never persisted, never invented)."""

import io
from dataclasses import dataclass

from docx import Document
from sqlalchemy import select

from app.models.student import StudentProfile
from app.services import resume_analysis_service
from app.services.auth_service import register_student
from app.services.resume_service import process_resume

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass
class _FakeUpload:
    filename: str
    content_type: str


def _make_profile(db_session, email="analysis@example.com") -> StudentProfile:
    user = register_student(db_session, email=email, password="Password1", full_name="Analysis Student")
    return db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))


def _docx_bytes(paragraphs: list[str]) -> bytes:
    document = Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _upload(db_session, profile, paragraphs: list[str], filename="resume.docx"):
    content = _docx_bytes(paragraphs)
    upload = _FakeUpload(filename=filename, content_type=DOCX_CONTENT_TYPE)
    return process_resume(db_session, profile, upload, content)


def test_strong_bullet_with_verb_and_metric_grades_strong(db_session):
    profile = _make_profile(db_session, "bullets-strong@example.com")
    resume = _upload(
        db_session,
        profile,
        [
            "SKILLS", "Python, SQL",
            "PROJECTS",
            "- Built a REST API using Python, cutting response latency by 40%.",
        ],
    )
    grades = resume_analysis_service.grade_bullets(resume)
    assert any(g.strength == resume_analysis_service.BULLET_STRONG for g in grades)
    strong = next(g for g in grades if g.strength == resume_analysis_service.BULLET_STRONG)
    assert strong.has_action_verb
    assert strong.has_metric
    assert strong.fix_suggestion is None


def test_vague_bullet_grades_weak_with_fix_suggestion(db_session):
    profile = _make_profile(db_session, "bullets-weak@example.com")
    resume = _upload(
        db_session,
        profile,
        [
            "SKILLS", "Python",
            "EXPERIENCE",
            "- Worked on backend development for the team.",
        ],
    )
    grades = resume_analysis_service.grade_bullets(resume)
    assert grades, "expected at least one bullet to be graded"
    weak = grades[0]
    assert weak.strength == resume_analysis_service.BULLET_WEAK
    assert weak.fix_suggestion is not None
    assert "worked on" in weak.fix_suggestion.lower()


def test_self_consistency_flags_skill_listed_but_never_evidenced(db_session):
    profile = _make_profile(db_session, "consistency-flag@example.com")
    resume = _upload(
        db_session,
        profile,
        [
            "SKILLS", "Python, Kubernetes",
            "PROJECTS",
            "- Built a data pipeline using Python for a course project.",
        ],
    )
    flags = resume_analysis_service.check_self_consistency(db_session, resume)
    flagged_names = {f.skill_name for f in flags}
    assert "Kubernetes" in flagged_names
    assert "Python" not in flagged_names


def test_self_consistency_no_flags_when_every_skill_is_backed_up(db_session):
    profile = _make_profile(db_session, "consistency-clean@example.com")
    resume = _upload(
        db_session,
        profile,
        [
            "SKILLS", "Python",
            "PROJECTS",
            "- Built a data pipeline using Python for a course project.",
        ],
    )
    flags = resume_analysis_service.check_self_consistency(db_session, resume)
    assert flags == []


def test_parseability_score_is_high_for_a_clean_well_sectioned_resume(db_session):
    profile = _make_profile(db_session, "parse-clean@example.com")
    resume = _upload(
        db_session,
        profile,
        [
            "SUMMARY", "Aspiring backend engineer with a passion for distributed systems and clean architecture.",
            "SKILLS", "Python, SQL, Git, Docker",
            "PROJECTS", "- Built a REST API using FastAPI and PostgreSQL for a university course project.",
            "EDUCATION", "B.Tech Computer Science, 2026",
        ],
    )
    result = resume_analysis_service.score_parseability(resume)
    assert result.score > 0.7
    assert result.warnings == []


def test_parseability_score_flags_near_empty_extraction(db_session):
    profile = _make_profile(db_session, "parse-thin@example.com")
    resume = _upload(db_session, profile, ["Ada"])
    result = resume_analysis_service.score_parseability(resume)
    assert result.score < 0.7
    assert result.warnings
