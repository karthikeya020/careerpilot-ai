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


def test_domains_endpoint_reports_recommendations_and_counts(client) -> None:
    headers = _register_and_auth(client, email="domains-meta@example.com")
    response = client.get("/api/v1/assessments/domains", headers=headers)
    assert response.status_code == 200
    domains = response.json()
    slugs = {d["slug"] for d in domains}
    assert {"sql", "python", "javascript", "dsa", "oop", "java"} <= slugs
    for d in domains:
        assert d["question_count"] > 0
        assert isinstance(d["recommended"], bool)


def test_activity_calendar_and_analytics_reflect_real_answers(client) -> None:
    headers = _register_and_auth(client, email="activity@example.com")
    start = client.post("/api/v1/assessments/attempts", headers=headers, json={"domain_slug": "oop"})
    body = start.json()
    attempt_id = body["attempt_id"]
    question = body["next_question"]

    submit = client.post(
        f"/api/v1/assessments/attempts/{attempt_id}/responses",
        headers=headers,
        json={"question_id": question["id"], "response_payload": {"selected_option_ids": []}},
    )
    assert submit.status_code == 200
    submitted = submit.json()
    assert submitted["response"]["explanation"]  # explanation is now surfaced immediately
    assert submitted["total_in_domain"] >= 15

    import datetime as dt

    year = dt.datetime.now(dt.timezone.utc).year
    calendar = client.get(f"/api/v1/assessments/activity-calendar?year={year}", headers=headers)
    assert calendar.status_code == 200
    days = calendar.json()
    assert len(days) >= 1
    today_str = dt.datetime.now(dt.timezone.utc).date().isoformat()
    today_entry = next((d for d in days if d["date"] == today_str), None)
    assert today_entry is not None
    assert today_entry["count"] >= 1

    day_detail = client.get(f"/api/v1/assessments/activity-calendar/{today_str}", headers=headers)
    assert day_detail.status_code == 200
    detail_items = day_detail.json()
    assert len(detail_items) >= 1
    assert detail_items[0]["domain_name"] == "Object-Oriented Programming"
    assert detail_items[0]["difficulty_band"] in ("easy", "medium", "hard")

    analytics = client.get("/api/v1/assessments/analytics", headers=headers)
    assert analytics.status_code == 200
    stats = analytics.json()
    assert stats["total_answered"] >= 1
    assert stats["current_streak_days"] >= 1
    assert any(d["domain"] == "Object-Oriented Programming" for d in stats["accuracy_by_domain"])
