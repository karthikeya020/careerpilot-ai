"""Deterministic demo-student seed.

Run with: python -m app.seed.seed_demo

Idempotent: if the demo account already exists it is deleted (cascades to
every dependent row via FK ondelete=CASCADE) and recreated fresh, so the demo
can always be reset to a known-good state before a presentation.

Deliberately reuses the real service layer (onboarding_service,
resume_service, job_description_service) instead of hand-crafting rows, so
the seeded data is produced by the same code path a real student exercises --
if the pipeline breaks, seeding breaks too, instead of silently drifting out
of sync.
"""

import io
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from docx import Document
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.assessment import Question
from app.models.audit import AuditEvent
from app.models.student import StudentProfile
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest, SelfAssessedSkill
from app.services.assessment_service import complete_attempt, start_attempt, submit_response
from app.services.auth_service import get_role_by_name
from app.services.job_description_service import create_job_description
from app.services.onboarding_service import complete_onboarding
from app.services.resume_service import process_resume

settings = get_settings()

DOCX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

DEMO_JOB_DESCRIPTION = """NimbusTech is hiring a Backend Engineering Intern.

Requirements:
- Currently pursuing a Bachelor's degree in Computer Science or related field
- 0-1 years of professional experience
- Strong programming skills in Python and SQL
- Experience with FastAPI and PostgreSQL
- Familiarity with Docker and Kubernetes
- Strong written and verbal communication skills

Responsibilities:
- Build and maintain REST APIs for internal tooling
- Collaborate with cross-functional teams on backend services
- Write clear technical documentation

Nice to have: exposure to GraphQL
"""


def _build_resume_docx() -> bytes:
    document = Document()
    document.add_paragraph("Aanya Sharma")
    document.add_paragraph("SUMMARY")
    document.add_paragraph(
        "Third-year Computer Science student passionate about backend systems and scalable APIs."
    )
    document.add_paragraph("SKILLS")
    document.add_paragraph("Python, SQL, Git, Docker, REST APIs, PostgreSQL")
    document.add_paragraph("PROJECTS")
    document.add_paragraph(
        "Developed a FastAPI-based task management service with PostgreSQL persistence and a Dockerized "
        "deployment, used by 50+ classmates during a university hackathon."
    )
    document.add_paragraph("EXPERIENCE")
    document.add_paragraph(
        "Teaching Assistant for Data Structures: mentored 30 students and led weekly problem-solving sessions."
    )
    document.add_paragraph("EDUCATION")
    document.add_paragraph("B.Tech in Computer Science, Expected 2027")
    document.add_paragraph("CERTIFICATIONS")
    document.add_paragraph("AWS Cloud Practitioner (in progress)")
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


@dataclass
class _FakeUploadFile:
    filename: str | None
    content_type: str | None


def _delete_existing_demo_user(db) -> None:
    existing = db.scalar(select(User).where(User.email == settings.demo_student_email))
    if existing is not None:
        db.delete(existing)
        db.commit()


def _seed_weak_sql_join_evidence(db, profile: StudentProfile):
    from app.services.mission_service import get_active_mission

    attempt = start_attempt(db, profile, "sql")

    relational_model_q = db.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="relational_model"))
    )
    inner_join_q = db.scalar(select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join")))

    if relational_model_q is not None:
        correct_ids = relational_model_q.correct_answer.get("correct_option_ids", [])
        submit_response(db, attempt, relational_model_q, {"selected_option_ids": correct_ids})

    if inner_join_q is not None and inner_join_q.options:
        wrong_option = next(
            o["id"] for o in inner_join_q.options if o["id"] not in inner_join_q.correct_answer["correct_option_ids"]
        )
        submit_response(db, attempt, inner_join_q, {"selected_option_ids": [wrong_option]})

    complete_attempt(db, profile, attempt)
    return get_active_mission(db, profile.id)


def seed_demo_student() -> None:
    db = SessionLocal()
    try:
        _delete_existing_demo_user(db)

        student_role = get_role_by_name(db, "student")
        user = User(
            email=settings.demo_student_email,
            password_hash=hash_password(settings.demo_student_password),
        )
        db.add(user)
        db.flush()

        from app.models.user import UserRole

        db.add(UserRole(user_id=user.id, role_id=student_role.id))
        profile = StudentProfile(user_id=user.id, full_name="Aanya Sharma", consent_settings={})
        db.add(profile)
        db.add(AuditEvent(user_id=user.id, event_type="user_registered", payload={"seed": True}))
        db.commit()
        db.refresh(profile)

        onboarding_payload = OnboardingRequest(
            full_name="Aanya Sharma",
            career_goal_description=(
                "Land a backend engineering internship at a product-based company within 6 months, with a "
                "focus on distributed systems fundamentals."
            ),
            timeline_months=6,
            target_role_title="Backend Engineering Intern",
            target_role_seniority="internship",
            self_assessed_skills=[
                SelfAssessedSkill(skill_name="Python", rating=0.75),
                SelfAssessedSkill(skill_name="SQL", rating=0.65),
                SelfAssessedSkill(skill_name="Communication", rating=0.3),
            ],
        )
        profile = complete_onboarding(db, profile, onboarding_payload)

        resume_bytes = _build_resume_docx()
        fake_upload = _FakeUploadFile(filename="aanya_sharma_resume.docx", content_type=DOCX_CONTENT_TYPE)
        resume = process_resume(db, profile, fake_upload, resume_bytes)

        job_description = create_job_description(
            db,
            profile,
            title="Backend Engineering Intern",
            company="NimbusTech",
            raw_text=DEMO_JOB_DESCRIPTION,
            source="pasted",
        )

        # Give the demo student a real, deliberately weak SQL JOIN evidence
        # point -- this is what makes the Phase 2 autonomous loop (CARE ->
        # GraphRAG root-cause -> mission -> resource recommendation) visible
        # immediately in a fresh demo, without any manual setup.
        mission = _seed_weak_sql_join_evidence(db, profile)

        print("Demo student seeded successfully.")
        print(f"  Email:    {settings.demo_student_email}")
        print(f"  Password: {settings.demo_student_password}")
        print(f"  Resume:   {resume.original_filename} ({resume.parsing_status})")
        print(f"  Job desc: {job_description.title} @ {job_description.company}")
        if mission is not None:
            print(f"  Mission:  {mission.title}")
            if mission.root_cause:
                print(f"  Root cause traced via: {mission.root_cause.get('graph_source', 'unknown')}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_student()
