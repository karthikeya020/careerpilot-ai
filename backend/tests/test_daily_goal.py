"""Tests for the Assessment daily-goal bar: goal -> domain mapping (company
names and role keywords), the deterministic per-day 5-question set, and a
daily item ticking off once its concept is practised today.
"""

from sqlalchemy import select

from app.models.assessment import AssessmentAttempt, Concept, Question, QuestionResponse
from app.models.student import StudentProfile
from app.models.user import User
from app.services import daily_goal_service


def _register(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Daily Goal Student"},
    )
    assert response.status_code in (200, 201)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _profile_for(db_session, email) -> StudentProfile:
    user = db_session.scalar(select(User).where(User.email == email))
    return db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))


def test_no_goal_returns_empty_set(client) -> None:
    headers = _register(client, "daily-none@example.com")
    body = client.get("/api/v1/assessments/daily-goal", headers=headers).json()
    assert body["goal"] is None
    assert body["questions"] == []
    assert body["completed_today"] == 0


def test_company_goal_maps_to_domains_and_returns_five(client) -> None:
    headers = _register(client, "daily-company@example.com")
    body = client.put(
        "/api/v1/assessments/daily-goal",
        headers=headers,
        json={"goal": "I want to be placed in Microsoft"},
    ).json()

    assert body["goal"] == "I want to be placed in Microsoft"
    # Every placement goal picks up DSA.
    assert "Data Structures & Algorithms" in body["matched_domains"]
    assert len(body["questions"]) == 5
    assert all(q["done_today"] is False for q in body["questions"])
    assert all(q["prompt"] and q["concept_slug"] for q in body["questions"])


def test_keyword_goal_without_company(client) -> None:
    headers = _register(client, "daily-keyword@example.com")
    body = client.put(
        "/api/v1/assessments/daily-goal",
        headers=headers,
        json={"goal": "crack a data analyst role"},
    ).json()
    assert {"SQL", "Python"} <= set(body["matched_domains"])
    assert len(body["questions"]) == 5


def test_daily_set_is_stable_within_the_day(client) -> None:
    headers = _register(client, "daily-stable@example.com")
    client.put("/api/v1/assessments/daily-goal", headers=headers, json={"goal": "SDE at Google"})
    first = client.get("/api/v1/assessments/daily-goal", headers=headers).json()
    second = client.get("/api/v1/assessments/daily-goal", headers=headers).json()
    assert [q["question_id"] for q in first["questions"]] == [q["question_id"] for q in second["questions"]]


def test_clearing_the_goal(client) -> None:
    headers = _register(client, "daily-clear@example.com")
    client.put("/api/v1/assessments/daily-goal", headers=headers, json={"goal": "Amazon SDE"})
    cleared = client.put("/api/v1/assessments/daily-goal", headers=headers, json={"goal": ""}).json()
    assert cleared["goal"] is None
    assert cleared["questions"] == []


def test_practising_a_daily_concept_marks_it_done(client, db_session) -> None:
    email = "daily-done@example.com"
    _register(client, email)
    profile = _profile_for(db_session, email)
    profile.assessment_goal = "I want to be placed in Microsoft"
    db_session.commit()

    goal = daily_goal_service.get_daily_goal(db_session, profile)
    assert goal.questions
    target = goal.questions[0]

    concept = db_session.scalar(select(Concept).where(Concept.slug == target.concept_slug))
    question = db_session.scalar(select(Question).where(Question.concept_id == concept.id))
    attempt = AssessmentAttempt(
        student_profile_id=profile.id, domain_id=concept.domain_id, status="completed"
    )
    db_session.add(attempt)
    db_session.flush()
    db_session.add(
        QuestionResponse(
            attempt_id=attempt.id,
            question_id=question.id,
            concept_id=concept.id,
            response_payload={},
            is_correct=True,
            score=1.0,
            ai_evaluated=False,
        )
    )
    db_session.commit()

    refreshed = daily_goal_service.get_daily_goal(db_session, profile)
    done = next(q for q in refreshed.questions if q.concept_slug == target.concept_slug)
    assert done.done_today is True
    assert refreshed.completed_today >= 1
