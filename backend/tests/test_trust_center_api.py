from sqlalchemy import select

import app.graphrag.service as graphrag_service
from app.models.assessment import Question
from app.models.student import StudentProfile
from app.services import assessment_service


def _register_and_auth(client, email="trust-center@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Trust Center Student"},
    )
    token = response.json()["access_token"]
    return token, response.json()


def test_trust_center_lists_and_details_care_executions(client, db_session) -> None:
    token, register_body = _register_and_auth(client)
    headers = {"Authorization": f"Bearer {token}"}

    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == register_body["user"]["id"]))
    question = db_session.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join"))
    )
    wrong_option = next(
        o["id"] for o in question.options if o["id"] not in question.correct_answer["correct_option_ids"]
    )
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    assessment_service.submit_response(db_session, attempt, question, {"selected_option_ids": [wrong_option]})
    assessment_service.complete_attempt(db_session, profile, attempt)

    executions = client.get("/api/v1/trust-center/executions", headers=headers)
    assert executions.status_code == 200
    body = executions.json()
    assert len(body) >= 1
    root_cause_exec = next(e for e in body if e["task_type"] == "root_cause_analysis")
    assert root_cause_exec["retrieval_used"] is True

    detail = client.get(f"/api/v1/trust-center/executions/{root_cause_exec['id']}", headers=headers)
    assert detail.status_code == 200
    detail_body = detail.json()
    assert len(detail_body["agent_runs"]) >= 1
    assert detail_body["routing_factors"]["task_type"] == "root_cause_analysis"

    graphrag_run = next(r for r in detail_body["agent_runs"] if r["agent_name"] == "graphrag")
    # Neo4j isn't reachable in the test sandbox, so this proves the Trust
    # Center API surfaces the *fallback* label, not just the happy path --
    # see test_graphrag.py for the equivalent real-Neo4j assertion.
    assert graphrag_run["output_payload"]["graph_source"] == "relational_fallback"


class _BrokenGraphRepository:
    def __init__(self, *args, **kwargs) -> None:
        raise RuntimeError("stub: simulated Neo4j query failure")


def test_trust_center_labels_relational_fallback_when_neo4j_query_fails(client, db_session, monkeypatch) -> None:
    monkeypatch.setattr(graphrag_service, "is_graph_available", lambda: True)
    monkeypatch.setattr(graphrag_service, "GraphRepository", _BrokenGraphRepository)
    # Even when Neo4j *reports* available, a repository failure must not
    # crash the request -- it should still land on the relational fallback
    # and label it correctly, proving resilience beyond the simple
    # is_graph_available() flag.
    token, register_body = _register_and_auth(client, email="trust-center-neo4j@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    profile = db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == register_body["user"]["id"]))
    question = db_session.scalar(
        select(Question).join(Question.concept).where(Question.concept.has(slug="inner_join"))
    )
    wrong_option = next(
        o["id"] for o in question.options if o["id"] not in question.correct_answer["correct_option_ids"]
    )
    attempt = assessment_service.start_attempt(db_session, profile, "sql")
    assessment_service.submit_response(db_session, attempt, question, {"selected_option_ids": [wrong_option]})
    assessment_service.complete_attempt(db_session, profile, attempt)

    executions = client.get("/api/v1/trust-center/executions", headers=headers)
    root_cause_exec = next(e for e in executions.json() if e["task_type"] == "root_cause_analysis")
    detail = client.get(f"/api/v1/trust-center/executions/{root_cause_exec['id']}", headers=headers)
    graphrag_run = next(r for r in detail.json()["agent_runs"] if r["agent_name"] == "graphrag")
    assert graphrag_run["output_payload"]["graph_source"] == "relational_fallback"


def test_trust_center_twin_explanation(client) -> None:
    token, _ = _register_and_auth(client, email="trust-center-2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    onboarding = client.post(
        "/api/v1/onboarding",
        headers=headers,
        json={
            "full_name": "Trust Center Student",
            "career_goal_description": "Become a backend engineer.",
            "timeline_months": 6,
            "target_role_title": "Backend Engineer",
            "target_role_seniority": "entry level",
            "self_assessed_skills": [{"skill_name": "Python", "rating": 0.7}],
        },
    )
    assert onboarding.status_code == 200

    twin = client.get("/api/v1/career-twin", headers=headers)
    assert twin.status_code == 200
    snapshot_id = twin.json()["id"]
    assert twin.json()["components"][0]["uncertainty"] is not None or twin.json()["components"][0]["status"] == "insufficient_evidence"

    explanation = client.get(f"/api/v1/trust-center/twin-explanation/{snapshot_id}", headers=headers)
    assert explanation.status_code == 200
    body = explanation.json()
    assert body["version"] == 1
    assert len(body["component_diffs"]) == 6
