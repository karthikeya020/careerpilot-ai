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
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from docx import Document
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.evaluation.ablations import run_full_ablation_suite
from app.models.assessment import Question
from app.models.audit import AuditEvent
from app.models.interview import (
    INTERVIEW_MODE_HR,
    INTERVIEW_MODE_RESUME,
    INTERVIEW_MODE_ROLE_SPECIFIC,
    INTERVIEW_MODE_TECHNICAL,
)
from app.models.job_description import JobDescription
from app.models.student import StudentProfile, TargetRole
from app.models.user import User
from app.schemas.onboarding import OnboardingRequest, SelfAssessedSkill
from app.services.assessment_service import complete_attempt, start_attempt, submit_response
from app.services.auth_service import get_role_by_name
from app.services.experiment_service import run_scenario
from app.services.interview_service import (
    complete_session,
    evaluate_answer,
    start_session,
    submit_answer,
)
from app.services.job_description_service import create_job_description
from app.services.onboarding_service import complete_onboarding
from app.services.resume_service import process_resume
from app.services.speech_to_text import register_demo_fixture

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


def _build_silent_wav(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """A real, valid, silent 16kHz mono WAV -- a safe preloaded audio fixture
    for the demo Interview Arena answer (never uploaded real speech, never a
    third-party recording)."""
    num_samples = int(duration_seconds * sample_rate)
    num_channels = 1
    bits_per_sample = 16
    byte_rate = sample_rate * num_channels * bits_per_sample // 8
    block_align = num_channels * bits_per_sample // 8
    data = b"\x00\x00" * num_samples
    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF", 36 + len(data), b"WAVE",
        b"fmt ", 16, 1, num_channels, sample_rate, byte_rate, block_align, bits_per_sample,
        b"data", len(data),
    )
    return header + data


_HR_ANSWER = (
    "In my last team project, a teammate and I disagreed on the database schema approach and it was "
    "slowing the team down close to a deadline. My task was to get us unblocked without escalating it "
    "into a bigger conflict. I set up a short call, asked them to walk me through their reasoning, and "
    "proposed we prototype both approaches for an hour and compare query performance directly instead of "
    "arguing in the abstract. As a result we picked a hybrid approach and shipped on time -- and I learned "
    "to lead with curiosity before disagreement, which was a mistake I'd made in earlier group projects."
)

_RESUME_ANSWER = (
    "The project I'm proudest of is the FastAPI-based task management service I built and shipped during a "
    "university hackathon -- I designed the REST API, modeled the PostgreSQL schema, and containerized the "
    "whole thing with Docker so classmates could run it locally without fighting dependency issues. Over 50 "
    "classmates ended up using it during the event. My specific contribution was the API layer and the "
    "database schema; a teammate handled the frontend. The trickiest part was getting concurrent task "
    "updates to not clobber each other, which I solved with optimistic locking on the task row version."
)


def _role_answer(role_title: str) -> str:
    return (
        f"I'm interested in the {role_title} role because it's squarely backend systems work -- building "
        f"and maintaining REST APIs, working with PostgreSQL, and thinking about how services scale -- "
        f"which is exactly the direction I want my career to go. I think the most important skills for "
        f"this role are strong SQL and API design fundamentals, clear technical communication with a "
        f"cross-functional team, and comfort with Docker-based deployment workflows; I've built all three "
        f"through coursework, a teaching-assistant role, and a hackathon project, though I know there's "
        f"always more depth to build."
    )


def _technical_answer_for(expected_keywords: list[str]) -> str:
    if "inner join" in expected_keywords:
        return (
            "An INNER JOIN returns only the rows where there is a match in both tables based on the join "
            "condition -- for example, joining orders to customers on customer_id only returns orders that "
            "have a matching customer. A LEFT JOIN keeps every row from the left table and fills in NULL "
            "for columns from the right table when there's no match, which is what I'd use when I want a "
            "full list of customers along with any orders they placed, including customers with zero orders."
        )
    if "group" in expected_keywords:
        return (
            "GROUP BY collapses rows that share the same value in one or more columns into a single output "
            "row per group, and it's almost always paired with an aggregate function like COUNT or SUM that "
            "runs separately within each group -- for example GROUP BY customer_id with SUM(order_total) "
            "gives total spend per customer instead of one row per order."
        )
    return (
        "A list comprehension is a concise way to build a new list by applying an expression to each item "
        "of an iterable, optionally filtering with a condition, all in a single readable line -- for "
        "example [x * 2 for x in values if x > 0]. I'd prefer it over a for loop when the transformation is "
        "simple enough to stay readable in one line; for more complex multi-step logic I'd still use a "
        "regular loop for readability."
    )


def _seed_interview_arena(db, profile: StudentProfile, job_description: JobDescription, target_role: TargetRole | None):
    """One fully completed 'mixed' mode interview -- real transcript (one
    audio fixture, three typed), real CARE-routed evaluations, real
    resume-claim evidence verification, real Interview Replay markers, and a
    real Career Twin update. Nothing here is a placeholder: every answer runs
    through the exact same service the live Interview Arena screen calls."""
    session = start_session(
        db, profile, mode="mixed",
        target_role_id=target_role.id if target_role else None,
        job_description_id=job_description.id,
    )
    role_title = target_role.title if target_role else "this role"

    for question in session.questions:
        if question.mode == INTERVIEW_MODE_TECHNICAL:
            transcript = _technical_answer_for(question.expected_keywords)
            audio_bytes = _build_silent_wav()
            register_demo_fixture(audio_bytes, transcript)
            answer = submit_answer(
                db, profile, question,
                audio_bytes=audio_bytes, audio_filename="answer.wav",
                audio_mime_type="audio/wav", audio_duration_seconds=14.0,
            )
        elif question.mode == INTERVIEW_MODE_RESUME:
            answer = submit_answer(db, profile, question, typed_answer_text=_RESUME_ANSWER)
        elif question.mode == INTERVIEW_MODE_ROLE_SPECIFIC:
            answer = submit_answer(db, profile, question, typed_answer_text=_role_answer(role_title))
        elif question.mode == INTERVIEW_MODE_HR:
            answer = submit_answer(db, profile, question, typed_answer_text=_HR_ANSWER)
        else:
            answer = submit_answer(db, profile, question, typed_answer_text=_HR_ANSWER)
        evaluate_answer(db, profile, session, question, answer)

    return complete_session(db, profile, session)


def _seed_experiment_lab(db, profile: StudentProfile, target_role: TargetRole | None):
    """Four real Experiment Lab scenarios (SQL, DSA, communication, and a
    mixed allocation) run through the exact deterministic `sim-v1` engine
    the live Experiment Lab screen uses -- so Competition Mode always has a
    real comparison to show, never a fabricated one."""
    role_id = target_role.id if target_role else None
    run_scenario(
        db, profile, "20h focused: SQL",
        [{"skill_name": "SQL", "activity_type": "practice_problems", "hours": 20}],
        target_role_id=role_id,
    )
    run_scenario(
        db, profile, "20h focused: Data Structures",
        [{"skill_name": "Data Structures", "activity_type": "practice_problems", "hours": 20}],
        target_role_id=role_id,
    )
    run_scenario(
        db, profile, "20h focused: Communication (mock interviews)",
        [{"skill_name": "Communication", "activity_type": "mock_interview", "hours": 20}],
        target_role_id=role_id,
    )
    run_scenario(
        db, profile, "Balanced 30h: SQL + Data Structures + Communication",
        [
            {"skill_name": "SQL", "activity_type": "practice_problems", "hours": 10},
            {"skill_name": "Data Structures", "activity_type": "practice_problems", "hours": 10},
            {"skill_name": "Communication", "activity_type": "mock_interview", "hours": 10},
        ],
        target_role_id=role_id,
    )


def _seed_research_lab(db, profile: StudentProfile) -> None:
    """One real run of the full Research Lab suite -- routing agreement,
    graph-vs-vector retrieval, and all three newly-harnessed ablations
    (Career Twin memory, reflection, consensus) -- so the Research Lab
    screen and Competition Mode's research step always have a real,
    reproducible result set for all six named ablation seams instead of an
    empty state. See app/evaluation/ablations.py and
    docs/research/FINAL_RESULTS_SUMMARY.md for methodology."""
    run_full_ablation_suite(db, student_profile_id=profile.id)


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

        target_role = db.scalar(select(TargetRole).where(TargetRole.student_profile_id == profile.id))

        # Competition Mode's interview, experiment, and research steps must
        # never show an empty state during the live presentation -- seed one
        # real completed interview, one real Experiment Lab comparison, and
        # one real Research Lab result set, all through the same service
        # layer (and, for research, the same evaluation module) the live
        # screens use.
        interview_session = _seed_interview_arena(db, profile, job_description, target_role)
        _seed_experiment_lab(db, profile, target_role)
        _seed_research_lab(db, profile)

        print("Demo student seeded successfully.")
        print(f"  Email:    {settings.demo_student_email}")
        print(f"  Password: {settings.demo_student_password}")
        print(f"  Resume:   {resume.original_filename} ({resume.parsing_status})")
        print(f"  Job desc: {job_description.title} @ {job_description.company}")
        if mission is not None:
            print(f"  Mission:  {mission.title}")
            if mission.root_cause:
                print(f"  Root cause traced via: {mission.root_cause.get('graph_source', 'unknown')}")
        print(
            f"  Interview: {interview_session.mode} session, "
            f"{len(interview_session.questions)} questions, "
            f"overall score {interview_session.overall_score}"
        )
        print("  Experiment Lab: 4 scenarios seeded (SQL, Data Structures, Communication, Balanced 30h)")
        print("  Research Lab: all 6 ablations run (CARE, graph, vector, memory, reflection, consensus)")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_student()
