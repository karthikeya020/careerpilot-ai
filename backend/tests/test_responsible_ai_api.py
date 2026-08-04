"""Responsible AI Center: overview (what's evaluated/not, versions,
evidence provenance, non-claims), data export, interview-audio deletion,
and full self-service account deletion.
"""

import io


def _register_and_auth(client, email="responsible-ai@example.com", password="Password1"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Responsible AI Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_overview_lists_non_claims_and_versions(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/responsible-ai/overview", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert any("hiring probability" in c.lower() for c in body["non_claims"])
    assert any("ranking" in c.lower() for c in body["non_claims"])
    assert body["versions"]["care_policy_version"] == "care-policy-v1"
    assert body["versions"]["career_twin_formula_version"] == "twin-v2"
    assert body["versions"]["simulation_engine_version"] == "sim-v1"
    assert "technical" in body["versions"]["agent_prompt_versions"]
    assert body["human_review"]["pending_count"] == 0
    assert body["stored_interview_audio_count"] == 0
    assert isinstance(body["evaluates"], list) and len(body["evaluates"]) > 0
    assert isinstance(body["does_not_evaluate"], list) and len(body["does_not_evaluate"]) > 0


def test_overview_requires_auth(client) -> None:
    response = client.get("/api/v1/responsible-ai/overview")
    assert response.status_code == 401


def test_export_contains_expected_sections(client) -> None:
    headers = _register_and_auth(client, email="export-test@example.com")
    response = client.get("/api/v1/responsible-ai/export", headers=headers)
    assert response.status_code == 200
    body = response.json()
    for key in ("profile", "resumes", "job_descriptions", "skill_evidence", "career_twin_snapshots", "missions", "audit_events"):
        assert key in body
    assert body["profile"]["full_name"] == "Responsible AI Student" or body["profile"]["full_name"]


def test_delete_interview_audio_clears_stored_files(client) -> None:
    headers = _register_and_auth(client, email="audio-deletion@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    fake_audio = io.BytesIO(b"not-a-real-audio-file")
    submit = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={"question_id": question["id"], "typed_answer_text": "I would communicate early and often."},
        files={"audio": ("answer.webm", fake_audio, "audio/webm")},
    )
    assert submit.status_code == 200
    assert submit.json()["answer"]["has_audio"] is True

    overview_before = client.get("/api/v1/responsible-ai/overview", headers=headers).json()
    assert overview_before["stored_interview_audio_count"] == 1

    deletion = client.delete("/api/v1/responsible-ai/interview-audio", headers=headers)
    assert deletion.status_code == 200
    assert deletion.json()["deleted_count"] == 1

    overview_after = client.get("/api/v1/responsible-ai/overview", headers=headers).json()
    assert overview_after["stored_interview_audio_count"] == 0

    # Transcript must survive audio deletion -- this is consent withdrawal, not full erasure.
    replay = client.get(f"/api/v1/interviews/sessions/{session_id}/replay", headers=headers)
    assert replay.json()["items"][0]["answer"]["transcript"]


def test_delete_account_requires_correct_password(client) -> None:
    headers = _register_and_auth(client, email="wrong-password-delete@example.com", password="Password1")
    response = client.request(
        "DELETE", "/api/v1/responsible-ai/account", headers=headers, json={"password": "WrongPassword1"}
    )
    assert response.status_code == 401


def test_delete_account_removes_all_data(client) -> None:
    headers = _register_and_auth(client, email="full-delete@example.com", password="Password1")
    client.post(
        "/api/v1/experiments/scenarios",
        headers=headers,
        json={"name": "Before deletion", "allocations": [{"skill_name": "SQL", "activity_type": "practice_problems", "hours": 10}]},
    )

    response = client.request("DELETE", "/api/v1/responsible-ai/account", headers=headers, json={"password": "Password1"})
    assert response.status_code == 204

    login = client.post("/api/v1/auth/login", json={"email": "full-delete@example.com", "password": "Password1"})
    assert login.status_code == 401


def test_cross_student_cannot_see_another_students_overview(client) -> None:
    headers_a = _register_and_auth(client, email="ra-owner@example.com")
    headers_b = _register_and_auth(client, email="ra-other@example.com")

    client.post(
        "/api/v1/experiments/scenarios",
        headers=headers_a,
        json={"name": "A's scenario", "allocations": [{"skill_name": "SQL", "activity_type": "practice_problems", "hours": 10}]},
    )

    export_b = client.get("/api/v1/responsible-ai/export", headers=headers_b).json()
    assert export_b["experiment_scenarios"] == []
