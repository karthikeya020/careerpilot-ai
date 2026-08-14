"""Recruiter-ready evidence card: score composition, the mandatory
disclaimer (Constitution rule 5 -- never a hiring verdict), and consent
gating for the recruiter-role view."""

import io
from dataclasses import dataclass

from docx import Document
from sqlalchemy import select

from app.models.student import StudentProfile
from app.services import recruiter_card_service, role_dashboard_service
from app.services.auth_service import register_student
from app.services.resume_service import get_latest_resume, process_resume

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


@dataclass
class _FakeUpload:
    filename: str
    content_type: str


def _make_profile(db_session, email="recruiter-card@example.com") -> StudentProfile:
    user = register_student(db_session, email=email, password="Password1", full_name="Card Student")
    return db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))


def _docx_bytes(paragraphs: list[str]) -> bytes:
    document = Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def _upload(db_session, profile, paragraphs: list[str]):
    content = _docx_bytes(paragraphs)
    upload = _FakeUpload(filename="resume.docx", content_type=DOCX_CONTENT_TYPE)
    return process_resume(db_session, profile, upload, content)


def test_no_resume_yields_has_resume_false_and_no_score():
    class _StubProfile:
        id = None

    card = recruiter_card_service.build_recruiter_card(None, _StubProfile(), None)
    assert card.has_resume is False
    assert card.trust_score is None


def test_card_always_carries_the_non_hiring_disclaimer(db_session):
    profile = _make_profile(db_session)
    resume = _upload(
        db_session,
        profile,
        [
            "SKILLS", "Python, SQL",
            "PROJECTS", "- Built a REST API using Python and SQL, cutting latency by 40%.",
        ],
    )
    card = recruiter_card_service.build_recruiter_card(db_session, profile, resume)
    assert card.has_resume is True
    assert 0.0 <= card.trust_score <= 1.0
    assert "not a hiring recommendation" in card.disclaimer.lower()
    assert "probability of being hired" in card.disclaimer.lower()


def test_card_flags_weak_bullets_and_unevidenced_skills_as_concerns(db_session):
    profile = _make_profile(db_session, "recruiter-card-weak@example.com")
    resume = _upload(
        db_session,
        profile,
        [
            "SKILLS", "Python, Kubernetes",
            "EXPERIENCE", "- Worked on backend development for the team.",
        ],
    )
    card = recruiter_card_service.build_recruiter_card(db_session, profile, resume)
    concerns_text = " ".join(card.concerns).lower()
    assert "kubernetes" in concerns_text


def _make_role_user(db_session, role_name: str, email: str) -> dict:
    from app.core.security import create_access_token, hash_password
    from app.models.user import Role, User, UserRole

    role = db_session.scalar(select(Role).where(Role.name == role_name))
    user = User(email=email, password_hash=hash_password("Password1"))
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(user.id, [role_name])
    return {"Authorization": f"Bearer {token}"}


def test_recruiter_endpoint_forbidden_until_student_opts_in_then_returns_card(client, db_session):
    student_register = client.post(
        "/api/v1/auth/register",
        json={"email": "consent-flow@example.com", "password": "Password1", "full_name": "Consent Flow Student"},
    )
    student_headers = {"Authorization": f"Bearer {student_register.json()['access_token']}"}
    student_profile = db_session.scalar(select(StudentProfile).order_by(StudentProfile.id.desc()))

    recruiter_headers = _make_role_user(db_session, "recruiter", "recruiter-card-view@example.com")

    before = client.get(
        f"/api/v1/recruiter/candidates/{student_profile.id}/evidence-card", headers=recruiter_headers
    )
    assert before.status_code == 403

    opt_in = client.put(
        "/api/v1/students/me/recruiter-visibility", headers=student_headers, json={"visible": True}
    )
    assert opt_in.status_code == 204

    after = client.get(
        f"/api/v1/recruiter/candidates/{student_profile.id}/evidence-card", headers=recruiter_headers
    )
    assert after.status_code == 200
    body = after.json()
    assert body["has_resume"] is False
    assert "not a hiring recommendation" in body["disclaimer"].lower()
