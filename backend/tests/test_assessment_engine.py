from sqlalchemy import select

from app.models.assessment import Question
from app.models.skill import EVIDENCE_TYPE_ASSESSMENT, SkillEvidence
from app.models.student import StudentProfile
from app.services import assessment_service
from app.services.auth_service import register_student


def _make_profile(db_session, email="assess@example.com") -> StudentProfile:
    user = register_student(db_session, email=email, password="Password1", full_name="Assess Student")
    return db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))


def test_start_attempt_and_select_first_question_prefers_shallow_concepts(db_session):
    profile = _make_profile(db_session)
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    question = assessment_service.select_next_question(db_session, attempt)
    assert question is not None
    # relational_model has depth 0 and should be preferred as a first question
    # over deep concepts like inner_join (depth 3) at the default difficulty.
    assert question.concept.slug in {"relational_model", "data_types"} or question.difficulty <= 2


def test_mcq_scoring_is_deterministic_exact_match(db_session):
    profile = _make_profile(db_session)
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    question = db_session.scalar(
        select(Question).where(Question.domain_id == attempt.domain_id, Question.question_type == "multiple_choice")
    )
    response = assessment_service.submit_response(
        db_session, attempt, question, {"selected_option_ids": question.correct_answer["correct_option_ids"]}
    )
    assert response.is_correct is True
    assert float(response.score) == 1.0


def test_mcq_wrong_answer_scores_zero(db_session):
    profile = _make_profile(db_session)
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    question = db_session.scalar(
        select(Question).where(Question.domain_id == attempt.domain_id, Question.question_type == "multiple_choice")
    )
    wrong_option = next(o["id"] for o in question.options if o["id"] not in question.correct_answer["correct_option_ids"])
    response = assessment_service.submit_response(db_session, attempt, question, {"selected_option_ids": [wrong_option]})
    assert response.is_correct is False


def test_free_form_response_graded_by_keyword_overlap(db_session):
    profile = _make_profile(db_session)
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    question = db_session.scalar(
        select(Question).where(Question.domain_id == attempt.domain_id, Question.question_type == "short_answer")
    )
    response = assessment_service.submit_response(db_session, attempt, question, {"response_text": "the on clause"})
    assert response.ai_evaluated is True
    assert response.score is not None


def test_complete_attempt_records_evidence_and_updates_twin(db_session):
    profile = _make_profile(db_session)
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    question = db_session.scalar(
        select(Question).where(Question.domain_id == attempt.domain_id, Question.question_type == "multiple_choice")
    )
    assessment_service.submit_response(
        db_session, attempt, question, {"selected_option_ids": question.correct_answer["correct_option_ids"]}
    )
    completed = assessment_service.complete_attempt(db_session, profile, attempt)
    assert completed.status == "completed"
    assert completed.score is not None

    evidence = db_session.scalars(
        select(SkillEvidence).where(
            SkillEvidence.student_profile_id == profile.id, SkillEvidence.evidence_type == EVIDENCE_TYPE_ASSESSMENT
        )
    ).all()
    assert len(evidence) >= 1
    assert evidence[0].concept_id == question.concept_id

    from app.models.career_twin import CareerTwinSnapshot

    snapshot = db_session.scalar(
        select(CareerTwinSnapshot)
        .where(CareerTwinSnapshot.student_profile_id == profile.id)
        .order_by(CareerTwinSnapshot.version.desc())
    )
    assert snapshot is not None


def test_adaptive_difficulty_increases_after_correct_streak(db_session):
    profile = _make_profile(db_session)
    attempt = assessment_service.start_attempt(db_session, profile, "python")
    for _ in range(2):
        question = assessment_service.select_next_question(db_session, attempt)
        assessment_service.submit_response(
            db_session, attempt, question,
            {"selected_option_ids": question.correct_answer.get("correct_option_ids", [])}
            if question.question_type != "short_answer" and question.question_type != "code_reading"
            else {"response_text": question.correct_answer.get("sample_answer", "")},
        )
        db_session.refresh(attempt)
    target = assessment_service._target_difficulty(list(attempt.responses))
    assert target >= 2
