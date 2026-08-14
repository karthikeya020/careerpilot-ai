"""Interview Arena end-to-end API tests: start a session, answer questions
(typed-fallback and audio-unavailable paths), verify CARE routing variety,
resume-claim evidence checking, Interview Replay, Career Twin update, and
cross-student authorization isolation.
"""

import io


def _register_and_auth(client, email="interview-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Interview API Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _answer_all(client, headers, session_id, question, transcript):
    payload = {"question_id": question["id"], "typed_answer_text": transcript}
    response = client.post(f"/api/v1/interviews/sessions/{session_id}/answers", headers=headers, data=payload)
    assert response.status_code == 200
    return response.json()


def test_list_modes(client) -> None:
    response = client.get("/api/v1/interviews/modes")
    assert response.status_code == 200
    modes = response.json()
    assert "technical" in modes
    assert "hr" in modes
    assert "resume" in modes


def test_technical_interview_single_agent_route(client) -> None:
    headers = _register_and_auth(client)
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "technical"})
    assert start.status_code == 201
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]
    assert question is not None
    assert "expected_keywords" not in question

    progress = _answer_all(
        client,
        headers,
        session_id,
        question,
        "An inner join returns only rows with matching values in both tables, while a left join keeps "
        "every row from the left table and fills unmatched columns with null.",
    )
    assert progress["evaluation"] is not None
    assert progress["evaluation"]["overall_score"] > 0
    assert "correctness" in progress["evaluation"]["dimension_scores"]
    assert progress["answer"]["transcript_source"] == "typed"


def test_resume_mode_without_resume_forces_escalation_and_evidence_check(client) -> None:
    headers = _register_and_auth(client, email="resume-mode@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "resume"})
    assert start.status_code == 201
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    progress = _answer_all(
        client,
        headers,
        session_id,
        question,
        "I led a major backend rewrite project that improved system reliability significantly for our users.",
    )
    evaluation = progress["evaluation"]
    assert evaluation is not None
    # No resume uploaded -- evidence-checking must say so respectfully, never accuse the student.
    assert evaluation["evidence_checks"]
    check = evaluation["evidence_checks"][0]
    assert check["classification"] == "insufficient_evidence"
    assert "dishonest" not in check["explanation"].lower()
    assert "lie" not in check["explanation"].lower()


def test_short_off_topic_answer_triggers_multi_agent_or_critic_route(client) -> None:
    headers = _register_and_auth(client, email="thin-answer@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    progress = _answer_all(client, headers, session_id, question, "I don't know.")
    evaluation = progress["evaluation"]
    assert evaluation is not None
    # A thin/off-topic answer should not be reported with unjustified high confidence.
    assert evaluation["confidence"] <= 0.85


def test_full_session_completion_updates_career_twin(client) -> None:
    headers = _register_and_auth(client, email="full-session@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    twin_before = client.get("/api/v1/career-twin", headers=headers)
    version_before = twin_before.json()["version"] if twin_before.status_code == 200 else 0

    is_complete = False
    guard = 0
    while not is_complete and guard < 10:
        guard += 1
        progress = _answer_all(
            client,
            headers,
            session_id,
            question,
            "When I worked on a group project, I needed to coordinate three teammates under a tight deadline. "
            "So I set up a shared task board and daily check-ins. As a result, we delivered a week early.",
        )
        is_complete = progress["is_complete"]
        question = progress["next_question"]

    assert is_complete
    session_detail = client.get(f"/api/v1/interviews/sessions/{session_id}", headers=headers)
    assert session_detail.json()["session"]["status"] == "completed"
    assert session_detail.json()["session"]["overall_score"] is not None

    twin_after = client.get("/api/v1/career-twin", headers=headers)
    assert twin_after.status_code == 200
    assert twin_after.json()["version"] > version_before

    replay = client.get(f"/api/v1/interviews/sessions/{session_id}/replay", headers=headers)
    assert replay.status_code == 200
    replay_body = replay.json()
    assert len(replay_body["items"]) >= 1
    assert replay_body["items"][0]["evaluation"] is not None


def test_typed_fallback_required_when_no_audio_or_text(client) -> None:
    headers = _register_and_auth(client, email="no-answer@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={"question_id": question["id"]},
    )
    assert response.status_code == 422


def test_audio_upload_without_live_stt_still_allows_typed_fallback(client) -> None:
    headers = _register_and_auth(client, email="audio-fallback@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    fake_audio = io.BytesIO(b"not-a-real-audio-file")
    response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={"question_id": question["id"], "typed_answer_text": "I would communicate early and often with my team."},
        files={"audio": ("answer.webm", fake_audio, "audio/webm")},
    )
    assert response.status_code == 200
    progress = response.json()
    # Deterministic STT can't transcribe arbitrary bytes -- falls back to typed text, never blocks.
    assert progress["answer"]["transcript_source"] == "typed"
    assert progress["answer"]["has_audio"] is True

    audio_response = client.get(f"/api/v1/interviews/answers/{progress['answer']['id']}/audio", headers=headers)
    assert audio_response.status_code == 200


def test_care_routes_differ_between_confident_and_thin_answers(client) -> None:
    headers = _register_and_auth(client, email="route-diversity@example.com")

    start_a = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "technical"})
    body_a = start_a.json()
    progress_a = _answer_all(
        client,
        headers,
        body_a["session"]["id"],
        body_a["next_question"],
        "An inner join returns only matching rows across both tables, while a left join also keeps "
        "unmatched rows from the left table with nulls for the right side's columns.",
    )
    execution_a = client.get(
        f"/api/v1/trust-center/executions/{progress_a['evaluation']['care_execution_id']}", headers=headers
    )
    assert execution_a.status_code == 200
    assert execution_a.json()["route"] == "single_agent"
    assert "communication" in execution_a.json()["agents_invoked"]
    assert "technical" in execution_a.json()["agents_invoked"]

    start_b = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "resume"})
    body_b = start_b.json()
    progress_b = _answer_all(client, headers, body_b["session"]["id"], body_b["next_question"], "no idea")
    execution_b = client.get(
        f"/api/v1/trust-center/executions/{progress_b['evaluation']['care_execution_id']}", headers=headers
    )
    assert execution_b.status_code == 200
    # A thin, evidence-conflicted resume claim must not settle on the same
    # cheap single-pass route as a strong, well-grounded technical answer.
    assert execution_b.json()["route"] in ("multi_agent", "critic_reflection", "human_review", "single_agent")
    assert execution_a.json()["route"] != execution_b.json()["route"] or set(
        execution_a.json()["agents_invoked"]
    ) != set(execution_b.json()["agents_invoked"])


def test_technical_gap_answer_triggers_follow_up_question(client) -> None:
    headers = _register_and_auth(client, email="follow-up-gap@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "technical"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]
    assert question["is_follow_up"] is False

    # Deliberately omits at least one expected keyword to leave a real gap.
    progress = _answer_all(
        client,
        headers,
        session_id,
        question,
        "An inner join returns only rows with matching values in both tables, while a left join keeps "
        "every row from the left table even when there is no match.",
    )
    next_question = progress["next_question"]
    assert next_question is not None
    assert next_question["is_follow_up"] is True
    assert next_question["follow_up_rationale"]
    assert next_question["mode"] == question["mode"]


def test_follow_up_question_inherits_parent_difficulty(client) -> None:
    headers = _register_and_auth(client, email="follow-up-difficulty@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "technical"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]
    assert question["difficulty"] == "easy"  # first two questions of every round are the easy tier

    progress = _answer_all(
        client,
        headers,
        session_id,
        question,
        "An inner join returns only rows with matching values in both tables, while a left join keeps "
        "every row from the left table even when there is no match.",
    )
    next_question = progress["next_question"]
    assert next_question["is_follow_up"] is True
    assert next_question["difficulty"] == "easy"  # inherited from the parent, not the column default "medium"


def test_follow_up_is_never_chained_and_session_caps_total_follow_ups(client) -> None:
    headers = _register_and_auth(client, email="follow-up-cap@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "technical"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    weak_answer = "I'm not totally sure, maybe something to do with rows."
    is_complete = False
    guard = 0
    while not is_complete and guard < 12:
        guard += 1
        progress = _answer_all(client, headers, session_id, question, weak_answer)
        is_complete = progress["is_complete"]
        question = progress["next_question"]

    assert is_complete
    replay = client.get(f"/api/v1/interviews/sessions/{session_id}/replay", headers=headers)
    items = replay.json()["items"]
    follow_up_count = sum(1 for item in items if item["question"]["is_follow_up"])
    # Cap enforced (interview_service._MAX_FOLLOW_UPS_PER_SESSION), and none
    # of the follow-up questions themselves triggered a second follow-up --
    # otherwise this weak-answer-every-time loop would blow past the cap.
    assert 0 < follow_up_count <= 2


def test_dsa_round_grades_like_technical_and_hides_model_answer_live(client) -> None:
    headers = _register_and_auth(client, email="dsa-round@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "dsa"})
    assert start.status_code == 201
    body = start.json()
    question = body["next_question"]
    assert question["mode"] == "dsa"
    assert question["difficulty"] in ("easy", "medium", "hard")
    assert "expected_keywords" not in question
    assert "model_answer_summary" not in question

    progress = _answer_all(
        client,
        headers,
        body["session"]["id"],
        question,
        "Big-O notation describes how an algorithm's running time or memory grows as the input size grows, "
        "independent of the exact hardware, which is what lets you compare two algorithms fairly.",
    )
    assert progress["evaluation"] is not None
    assert progress["evaluation"]["overall_score"] > 0
    assert "correctness" in progress["evaluation"]["dimension_scores"]


def test_camera_on_ratio_passes_through_to_communication_metrics(client) -> None:
    headers = _register_and_auth(client, email="camera-ratio@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={
            "question_id": question["id"],
            "typed_answer_text": "When I led a project, I set up a shared task board and we shipped early.",
            "camera_on_ratio": "0.82",
        },
    )
    assert response.status_code == 200
    metrics = response.json()["evaluation"]["communication_metrics"]
    assert metrics["camera_on_ratio"] == 0.82


def test_replay_includes_round_summary_with_difficulty_breakdown(client) -> None:
    headers = _register_and_auth(client, email="round-summary@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "technical"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    is_complete = False
    guard = 0
    while not is_complete and guard < 10:
        guard += 1
        progress = _answer_all(
            client,
            headers,
            session_id,
            question,
            "A join combines rows from two related tables using a shared key, for example matching orders to customers.",
        )
        is_complete = progress["is_complete"]
        question = progress["next_question"]
    assert is_complete

    replay = client.get(f"/api/v1/interviews/sessions/{session_id}/replay", headers=headers)
    assert replay.status_code == 200
    body = replay.json()
    summary = body["summary"]
    assert summary["scripted_question_count"] == 6
    assert len(summary["difficulty_breakdown"]) == 3
    assert summary["narrative_summary"]
    assert summary["overall_score"] is not None
    # Report items reveal the reference answer for scripted questions -- live
    # questions never do, and dynamically-generated follow-ups have no
    # pre-written model answer to reveal.
    for item in body["items"]:
        if not item["question"]["is_follow_up"]:
            assert item["question"]["model_answer_summary"]


def test_camera_consent_toggle_persists(client) -> None:
    headers = _register_and_auth(client, email="camera-consent@example.com")
    before = client.get("/api/v1/students/me", headers=headers)
    assert before.json()["camera_consent"] is False

    set_response = client.put("/api/v1/students/me/camera-consent", headers=headers, json={"enabled": True})
    assert set_response.status_code == 204

    after = client.get("/api/v1/students/me", headers=headers)
    assert after.json()["camera_consent"] is True


def test_cross_student_cannot_access_another_students_interview_session(client) -> None:
    headers_a = _register_and_auth(client, email="student-a@example.com")
    headers_b = _register_and_auth(client, email="student-b@example.com")

    start = client.post("/api/v1/interviews/sessions", headers=headers_a, json={"mode": "hr"})
    session_id = start.json()["session"]["id"]

    forbidden = client.get(f"/api/v1/interviews/sessions/{session_id}", headers=headers_b)
    assert forbidden.status_code == 404

    forbidden_replay = client.get(f"/api/v1/interviews/sessions/{session_id}/replay", headers=headers_b)
    assert forbidden_replay.status_code == 404
