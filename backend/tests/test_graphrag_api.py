"""API-level GraphRAG tests: the student-overview graph, on-demand concept
insight, and the embedded practice loop that must never redirect to the
Assessment Arena (see frontend/app/graphrag/page.tsx)."""


def _register_and_auth(client, email="graphrag-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "GraphRAG API Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_student_overview_endpoint_returns_the_whole_graph(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/graph/student-overview", headers=headers)
    assert response.status_code == 200
    body = response.json()

    domain_slugs = {n["domain_slug"] for n in body["nodes"]}
    assert {"sql", "python", "javascript", "dsa", "oop", "java"} <= domain_slugs
    assert body["total_concepts"] >= 35
    assert len(body["edges"]) > 0
    assert len(body["skills"]) >= 6
    # A brand-new student has no evidence anywhere yet -- honest, not faked.
    assert body["weaknesses"] == []
    assert body["overall_mastery"] is None


def test_concept_insight_endpoint_404s_for_unknown_concept(client) -> None:
    headers = _register_and_auth(client, email="graphrag-404@example.com")
    response = client.get("/api/v1/graph/concept/not-a-real-concept/insight", headers=headers)
    assert response.status_code == 404


def test_concept_insight_endpoint_returns_detail_for_a_real_concept(client) -> None:
    headers = _register_and_auth(client, email="graphrag-insight@example.com")
    response = client.get("/api/v1/graph/concept/abstraction/insight", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["concept_slug"] == "abstraction"
    assert body["status"] == "unknown"
    assert body["evidence_count"] == 0
    assert body["reasoning"]


def test_embedded_practice_flow_never_touches_assessment_endpoints_and_updates_twin(client) -> None:
    headers = _register_and_auth(client, email="graphrag-practice@example.com")

    twin_before = client.get("/api/v1/career-twin", headers=headers)
    version_before = twin_before.json()["version"] if twin_before.status_code == 200 else 0

    start = client.post("/api/v1/graph/practice/oop_basics/start", headers=headers)
    assert start.status_code == 200
    body = start.json()
    assert body["concept_slug"] == "oop_basics"
    assert body["total_in_concept"] >= 3
    attempt_id = body["attempt_id"]
    question = body["next_question"]
    assert question is not None
    assert "correct_answer" not in question  # never leak the rubric

    is_complete = False
    guard = 0
    while not is_complete and question is not None:
        guard += 1
        assert guard < 10
        if question["question_type"] in ("multiple_choice", "multiple_selection"):
            payload = {"question_id": question["id"], "response_payload": {"selected_option_ids": []}}
        else:
            payload = {"question_id": question["id"], "response_payload": {"response_text": "an answer"}}
        answer = client.post(
            f"/api/v1/graph/practice/oop_basics/attempts/{attempt_id}/answer", headers=headers, json=payload
        )
        assert answer.status_code == 200
        progress = answer.json()
        assert "explanation" in progress and progress["explanation"]  # immediate learning payoff
        is_complete = progress["is_complete"]
        question = progress["next_question"]

    assert is_complete

    twin_after = client.get("/api/v1/career-twin", headers=headers)
    assert twin_after.status_code == 200
    assert twin_after.json()["version"] > version_before

    overview = client.get("/api/v1/graph/student-overview", headers=headers).json()
    node = next(n for n in overview["nodes"] if n["slug"] == "oop_basics")
    assert node["status"] != "unknown"
    assert node["evidence_count"] >= 1


def test_practice_session_cannot_be_hijacked_by_another_student(client) -> None:
    headers_a = _register_and_auth(client, email="graphrag-owner@example.com")
    headers_b = _register_and_auth(client, email="graphrag-intruder@example.com")

    start = client.post("/api/v1/graph/practice/encapsulation/start", headers=headers_a)
    attempt_id = start.json()["attempt_id"]
    question = start.json()["next_question"]

    hijack = client.post(
        f"/api/v1/graph/practice/encapsulation/attempts/{attempt_id}/answer",
        headers=headers_b,
        json={"question_id": question["id"], "response_payload": {"selected_option_ids": []}},
    )
    assert hijack.status_code == 404
