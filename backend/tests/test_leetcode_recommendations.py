"""Tests for the weakness -> LeetCode problem recommender.

Covers: the no-history profile fallback (source="profile"), a fabricated
weak concept driving concept-targeted picks (source="assessment"), and
static-catalog integrity (slugs and difficulty labels well formed).
"""

from sqlalchemy import select

from app.data.leetcode_catalog import CONCEPT_PROBLEMS, DOMAIN_PROBLEMS, problem_url
from app.models.assessment import AssessmentAttempt, Concept, Question, QuestionResponse
from app.models.student import StudentProfile
from app.models.user import User
from app.services import leetcode_recommendation_service


def _register(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "LC Recs Student"},
    )
    assert response.status_code in (200, 201)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _profile_for(db_session, email) -> StudentProfile:
    user = db_session.scalar(select(User).where(User.email == email))
    return db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))


def test_profile_fallback_when_no_assessment_history(client) -> None:
    headers = _register(client, "lc-recs-fresh@example.com")
    response = client.get("/api/v1/assessments/leetcode-recommendations", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["source"] == "profile"
    assert body["groups"], "expected starter groups even with no history"
    for group in body["groups"]:
        assert group["accuracy"] is None
        assert group["problems"]
        for problem in group["problems"]:
            assert problem["url"] == f"https://leetcode.com/problems/{problem['slug']}/"
            assert problem["difficulty"] in {"Easy", "Medium", "Hard"}


def test_weak_concept_drives_targeted_recommendations(client, db_session) -> None:
    email = "lc-recs-weak@example.com"
    _register(client, email)
    profile = _profile_for(db_session, email)

    concept = db_session.scalar(select(Concept).where(Concept.slug == "arrays_strings"))
    questions = db_session.scalars(
        select(Question).where(Question.concept_id == concept.id).limit(3)
    ).all()
    assert len(questions) >= 2

    attempt = AssessmentAttempt(
        student_profile_id=profile.id, domain_id=concept.domain_id, status="completed"
    )
    db_session.add(attempt)
    db_session.flush()
    for question in questions:
        db_session.add(
            QuestionResponse(
                attempt_id=attempt.id,
                question_id=question.id,
                concept_id=concept.id,
                response_payload={},
                is_correct=False,
                score=0.0,
                ai_evaluated=False,
            )
        )
    db_session.commit()

    result = leetcode_recommendation_service.recommend(db_session, profile)

    assert result.source == "assessment"
    weak_group = next(g for g in result.groups if g.concept_slug == "arrays_strings")
    assert weak_group.accuracy == 0.0
    assert weak_group.answered == len(questions)
    assert weak_group.problems
    assert weak_group.problems[0].difficulty == "Easy"  # easiest-first ordering
    assert all(p.url.startswith("https://leetcode.com/problems/") for p in weak_group.problems)


def test_strong_performance_yields_no_weaknesses_source(client, db_session) -> None:
    email = "lc-recs-strong@example.com"
    _register(client, email)
    profile = _profile_for(db_session, email)

    concept = db_session.scalar(select(Concept).where(Concept.slug == "arrays_strings"))
    questions = db_session.scalars(
        select(Question).where(Question.concept_id == concept.id).limit(3)
    ).all()
    attempt = AssessmentAttempt(
        student_profile_id=profile.id, domain_id=concept.domain_id, status="completed"
    )
    db_session.add(attempt)
    db_session.flush()
    for question in questions:
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

    result = leetcode_recommendation_service.recommend(db_session, profile)
    assert result.source == "no_weaknesses"


def test_static_catalog_is_well_formed() -> None:
    for mapping in (CONCEPT_PROBLEMS, DOMAIN_PROBLEMS):
        for key, problems in mapping.items():
            assert problems, f"empty problem list for {key}"
            for slug, title, difficulty in problems:
                assert slug == slug.lower() and " " not in slug, f"bad slug {slug!r} under {key}"
                assert difficulty in {"Easy", "Medium", "Hard"}, f"bad difficulty {difficulty!r} for {slug}"
                assert title.strip()
                assert problem_url(slug) == f"https://leetcode.com/problems/{slug}/"
