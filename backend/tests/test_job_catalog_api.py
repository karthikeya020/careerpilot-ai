"""API-level Job Match tests: search/recommend/track endpoints and the
tracked-job cap surfacing as a real HTTP 409, not a crash."""


def _register_and_auth(client, email="jobmatch-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Job Match API Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_sectors_endpoint_lists_all_six_with_ten_each(client) -> None:
    response = client.get("/api/v1/job-catalog/sectors")
    assert response.status_code == 200
    sectors = response.json()
    assert {s["slug"] for s in sectors} == {"faang", "startup", "research", "government", "consulting", "finance"}
    assert all(s["listing_count"] == 10 for s in sectors)


def test_recommended_endpoint_requires_auth_and_returns_ten(client) -> None:
    anon = client.get("/api/v1/job-catalog/recommended")
    assert anon.status_code == 401

    headers = _register_and_auth(client, "recommended-api@example.com")
    response = client.get("/api/v1/job-catalog/recommended", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 10


def test_search_endpoint_pads_a_specific_company_search_to_ten(client) -> None:
    headers = _register_and_auth(client, "search-api@example.com")
    response = client.get("/api/v1/job-catalog/search?company=Amazon", headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 10
    assert results[0]["listing"]["company"] == "Amazon"
    for r in results:
        assert "readiness" in r
        assert "is_tracked" in r


def test_track_untrack_and_cap_roundtrip_through_the_api(client) -> None:
    headers = _register_and_auth(client, "track-api@example.com")
    search = client.get("/api/v1/job-catalog/search?sector=startup", headers=headers)
    listing_ids = [item["listing"]["id"] for item in search.json()]
    assert len(listing_ids) >= 6

    for listing_id in listing_ids[:5]:
        resp = client.post(f"/api/v1/job-catalog/tracked/{listing_id}", headers=headers)
        assert resp.status_code == 201
        assert resp.json()["match"]["is_tracked"] is True

    over_cap = client.post(f"/api/v1/job-catalog/tracked/{listing_ids[5]}", headers=headers)
    assert over_cap.status_code == 409

    tracked = client.get("/api/v1/job-catalog/tracked", headers=headers)
    assert tracked.status_code == 200
    assert len(tracked.json()) == 5

    remove = client.delete(f"/api/v1/job-catalog/tracked/{listing_ids[0]}", headers=headers)
    assert remove.status_code == 204

    now_ok = client.post(f"/api/v1/job-catalog/tracked/{listing_ids[5]}", headers=headers)
    assert now_ok.status_code == 201


def test_gap_plan_endpoint_returns_an_honest_estimate(client) -> None:
    headers = _register_and_auth(client, "gap-api@example.com")
    search = client.get("/api/v1/job-catalog/search?company=Zerodha", headers=headers)
    listing_id = search.json()[0]["listing"]["id"]

    response = client.get(f"/api/v1/job-catalog/{listing_id}/gap-plan?weekly_hours=8", headers=headers)
    assert response.status_code == 200
    plan = response.json()
    assert plan["weekly_commitment_hours"] == 8
    assert plan["missing_count"] > 0
    assert plan["total_estimated_hours"] > 0
    assert plan["estimated_weeks_to_ready"] > 0
    assert len(plan["items"]) == plan["missing_count"] + plan["partial_count"]
    assert any("heuristic" in a.lower() for a in plan["assumptions"])


def test_tracked_jobs_are_isolated_between_students_via_api(client) -> None:
    headers_a = _register_and_auth(client, "isolation-api-a@example.com")
    headers_b = _register_and_auth(client, "isolation-api-b@example.com")

    search = client.get("/api/v1/job-catalog/search?sector=finance", headers=headers_a)
    listing_id = search.json()[0]["listing"]["id"]
    client.post(f"/api/v1/job-catalog/tracked/{listing_id}", headers=headers_a)

    tracked_a = client.get("/api/v1/job-catalog/tracked", headers=headers_a).json()
    tracked_b = client.get("/api/v1/job-catalog/tracked", headers=headers_b).json()
    assert len(tracked_a) == 1
    assert len(tracked_b) == 0
