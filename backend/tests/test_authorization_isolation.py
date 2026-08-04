"""Proves one student cannot read or mutate another student's Phase 2
records through any ID-addressable endpoint: assessments, CARE executions,
Career Twin snapshots, missions, and job descriptions. Evidence and agent
runs have no standalone by-ID endpoint (they're only ever returned embedded
inside a caller-scoped parent resource), so there is no separate IDOR
surface to test for them directly -- this file exercises every route in
app/api/*.py that takes an object ID and belongs to a specific student.
"""

from sqlalchemy import select

from app.models.assessment import Question
from app.models.student import StudentProfile
from app.services import assessment_service


def _register(client, email):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Isolation Test Student"},
    )
    body = response.json()
    return body["access_token"], body["user"]["id"]


def _build_victim_records(client, db_session, token, user_id):
    """Student B: complete an onboarding + a failed-INNER-JOIN assessment
    attempt so a mission, a CareExecution/AgentRun pair, and a second Career
    Twin snapshot all exist to attempt to steal."""
    headers = {"Authorization": f"Bearer {token}"}
    client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "full_name": "Victim Student",
            "career_goal_description": "Become a backend engineer.",
            "timeline_months": 6,
            "target_role_title": "Backend Engineer",
            "target_role_seniority": "entry level",
            "self_assessed_skills": [{"skill_name": "SQL", "rating": 0.5}],
        },
    )
    jd = client.post(
        "/api/v1/job-descriptions",
        headers=headers,
        json={
            "title": "Victim Role",
            "company": "VictimCo",
            "raw_text": "Looking for a backend engineer with strong SQL and Python skills for a growing team.",
        },
    ).json()

    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))
    question = db_session.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join"))
    )
    wrong_option = next(
        o["id"] for o in question.options if o["id"] not in question.correct_answer["correct_option_ids"]
    )
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    assessment_service.submit_response(db_session, attempt, question, {"selected_option_ids": [wrong_option]})
    assessment_service.complete_attempt(db_session, profile, attempt)

    dashboard = client.get("/api/v1/dashboard", headers=headers).json()
    twin_history = client.get("/api/v1/career-twin/history", headers=headers).json()
    executions = client.get("/api/v1/trust-center/executions", headers=headers).json()

    return {
        "attempt_id": str(attempt.id),
        "mission_id": dashboard["mission"]["id"],
        "snapshot_id": twin_history[0]["id"],
        "execution_id": next(e["id"] for e in executions if e["task_type"] == "root_cause_analysis"),
        "job_description_id": jd["id"],
    }


def test_student_cannot_read_another_students_assessment_attempt(client, db_session) -> None:
    attacker_token, _ = _register(client, "attacker@example.com")
    victim_token, victim_id = _register(client, "victim@example.com")
    victim = _build_victim_records(client, db_session, victim_token, victim_id)

    response = client.get(
        f"/api/v1/assessments/attempts/{victim['attempt_id']}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert response.status_code == 404

    own = client.get(
        f"/api/v1/assessments/attempts/{victim['attempt_id']}",
        headers={"Authorization": f"Bearer {victim_token}"},
    )
    assert own.status_code == 200


def test_student_cannot_read_another_students_care_execution(client, db_session) -> None:
    attacker_token, _ = _register(client, "attacker2@example.com")
    victim_token, victim_id = _register(client, "victim2@example.com")
    victim = _build_victim_records(client, db_session, victim_token, victim_id)

    response = client.get(
        f"/api/v1/trust-center/executions/{victim['execution_id']}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert response.status_code == 404

    listing = client.get(
        "/api/v1/trust-center/executions", headers={"Authorization": f"Bearer {attacker_token}"}
    ).json()
    assert victim["execution_id"] not in [e["id"] for e in listing]


def test_student_cannot_read_another_students_twin_explanation(client, db_session) -> None:
    attacker_token, _ = _register(client, "attacker3@example.com")
    victim_token, victim_id = _register(client, "victim3@example.com")
    victim = _build_victim_records(client, db_session, victim_token, victim_id)

    response = client.get(
        f"/api/v1/trust-center/twin-explanation/{victim['snapshot_id']}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert response.status_code == 404


def test_student_cannot_complete_another_students_mission(client, db_session) -> None:
    attacker_token, _ = _register(client, "attacker4@example.com")
    victim_token, victim_id = _register(client, "victim4@example.com")
    victim = _build_victim_records(client, db_session, victim_token, victim_id)

    response = client.post(
        f"/api/v1/missions/{victim['mission_id']}/complete",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert response.status_code == 404


def test_student_cannot_read_another_students_job_description_or_match(client, db_session) -> None:
    attacker_token, _ = _register(client, "attacker5@example.com")
    victim_token, victim_id = _register(client, "victim5@example.com")
    victim = _build_victim_records(client, db_session, victim_token, victim_id)

    get_response = client.get(
        f"/api/v1/job-descriptions/{victim['job_description_id']}",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert get_response.status_code == 404

    match_response = client.get(
        f"/api/v1/job-descriptions/{victim['job_description_id']}/match",
        headers={"Authorization": f"Bearer {attacker_token}"},
    )
    assert match_response.status_code == 404

    own_list = client.get(
        "/api/v1/job-descriptions", headers={"Authorization": f"Bearer {attacker_token}"}
    ).json()
    assert own_list == []


def test_student_dashboard_never_shows_another_students_mission(client, db_session) -> None:
    attacker_token, _ = _register(client, "attacker6@example.com")
    victim_token, victim_id = _register(client, "victim6@example.com")
    victim = _build_victim_records(client, db_session, victim_token, victim_id)

    dashboard = client.get(
        "/api/v1/dashboard", headers={"Authorization": f"Bearer {attacker_token}"}
    ).json()
    mission = dashboard.get("mission")
    assert mission is None or mission["id"] != victim["mission_id"]


def test_protected_endpoint_rejects_missing_or_malformed_token(client) -> None:
    unauthenticated = client.get("/api/v1/dashboard")
    assert unauthenticated.status_code == 401

    garbage = client.get("/api/v1/dashboard", headers={"Authorization": "Bearer not-a-real-token"})
    assert garbage.status_code == 401
