"""Interview round-generation tests: every round is exactly 2 easy / 2
medium / 2 hard scripted questions (interview_service._generate_questions),
DSA carries the same rubric shape as Technical, and role/company templates
are fully substituted -- no leftover "{role}"/"{company}" placeholders.
"""

from sqlalchemy import select

from app.models.interview import (
    ALL_INTERVIEW_MODES,
    INTERVIEW_MODE_COMPANY_CONTEXT,
    INTERVIEW_MODE_DSA,
    INTERVIEW_MODE_MIXED,
    INTERVIEW_MODE_ROLE_SPECIFIC,
)
from app.models.student import StudentProfile
from app.services import interview_service
from app.services.auth_service import register_student


def _make_student_profile(db_session, email: str) -> StudentProfile:
    user = register_student(db_session, email=email, password="Password1", full_name="Test Student")
    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))
    assert profile is not None
    return profile


def test_every_mode_generates_exactly_two_of_each_difficulty(db_session):
    profile = _make_student_profile(db_session, "round-shape@example.com")
    for mode in ALL_INTERVIEW_MODES:
        session = interview_service.start_session(db_session, profile, mode=mode)
        db_session.refresh(session)
        questions = sorted(session.questions, key=lambda q: q.order_index)
        assert len(questions) == 6, mode
        assert [q.difficulty for q in questions] == ["easy", "easy", "medium", "medium", "hard", "hard"], mode
        # "mixed" blends HR/Technical questions rather than tagging them "mixed".
        expected_modes = {"hr", "technical"} if mode == INTERVIEW_MODE_MIXED else {mode}
        assert all(q.mode in expected_modes for q in questions)
        assert all(not q.is_follow_up for q in questions)
        assert all(q.model_answer_summary for q in questions), mode


def test_dsa_questions_carry_expected_keywords_and_model_answers(db_session):
    profile = _make_student_profile(db_session, "dsa-bank@example.com")
    session = interview_service.start_session(db_session, profile, mode=INTERVIEW_MODE_DSA)
    db_session.refresh(session)
    for question in session.questions:
        assert question.mode == INTERVIEW_MODE_DSA
        assert question.expected_keywords
        assert question.model_answer_summary


def test_mixed_mode_alternates_hr_and_technical(db_session):
    profile = _make_student_profile(db_session, "mixed-blend@example.com")
    session = interview_service.start_session(db_session, profile, mode=INTERVIEW_MODE_MIXED)
    db_session.refresh(session)
    questions = sorted(session.questions, key=lambda q: q.order_index)
    assert [q.mode for q in questions] == ["hr", "technical", "hr", "technical", "hr", "technical"]


def test_role_and_company_placeholders_are_fully_substituted(db_session):
    profile = _make_student_profile(db_session, "template-fill@example.com")
    for mode in (INTERVIEW_MODE_ROLE_SPECIFIC, INTERVIEW_MODE_COMPANY_CONTEXT):
        session = interview_service.start_session(db_session, profile, mode=mode)
        db_session.refresh(session)
        for question in session.questions:
            assert "{role}" not in question.prompt
            assert "{company}" not in question.prompt
            assert "{role}" not in question.model_answer_summary
            assert "{company}" not in question.model_answer_summary
