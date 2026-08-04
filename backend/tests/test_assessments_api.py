def _register_and_auth(client, email="assess-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Assess API Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_full_assessment_flow_through_api(client) -> None:
    headers = _register_and_auth(client)

    domains = client.get("/api/v1/assessments/domains", headers=headers)
    assert domains.status_code == 200
    assert any(d["slug"] == "sql" for d in domains.json())

    start = client.post("/api/v1/assessments/attempts", headers=headers, json={"domain_slug": "sql"})
    assert start.status_code == 200
    body = start.json()
    attempt_id = body["attempt_id"]
    assert body["next_question"] is not None
    assert "correct_answer" not in body["next_question"]

    # Answer questions until the attempt completes (bounded loop to avoid an
    # infinite test if something regresses).
    next_question = body["next_question"]
    for _ in range(30):
        if next_question is None:
            break
        if next_question["question_type"] in ("multiple_choice", "multiple_selection"):
            payload = {"question_id": next_question["id"], "response_payload": {"selected_option_ids": []}}
        else:
            payload = {"question_id": next_question["id"], "response_payload": {"response_text": "on clause"}}
        submit = client.post(f"/api/v1/assessments/attempts/{attempt_id}/responses", headers=headers, json=payload)
        assert submit.status_code == 200
        progress = submit.json()
        next_question = progress["next_question"]
        if progress["is_complete"]:
            break

    attempt = client.get(f"/api/v1/assessments/attempts/{attempt_id}", headers=headers)
    assert attempt.status_code == 200
    assert attempt.json()["status"] == "completed"
