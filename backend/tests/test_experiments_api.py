"""Career Experiment Lab API: scenario creation, side-by-side comparison,
the mandatory disclaimer, and cross-student authorization isolation.
"""


def _register_and_auth(client, email="experiment-api@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Experiment API Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_activity_types(client) -> None:
    response = client.get("/api/v1/experiments/activity-types")
    assert response.status_code == 200
    types = response.json()
    assert "practice_problems" in types
    assert "mock_interview" in types


def test_run_scenario_returns_result_with_disclaimer(client) -> None:
    headers = _register_and_auth(client)

    response = client.post(
        "/api/v1/experiments/scenarios",
        headers=headers,
        json={
            "name": "20 hours SQL",
            "allocations": [{"skill_name": "SQL", "activity_type": "practice_problems", "hours": 20}],
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["result"] is not None
    assert body["result"]["engine_version"] == "sim-v1"
    assert body["result"]["disclaimer"] == "Personalized scenario estimate—not a guaranteed outcome or hiring prediction."
    assert len(body["result"]["component_changes"]) == 1
    change = body["result"]["component_changes"][0]
    assert change["component_type"] == "technical_readiness"
    assert change["delta"] > 0
    assert "assumptions" in body["result"]
    assert len(body["result"]["assumptions"]) > 0
    # The explanation must restate the same numbers, never contradict them --
    # spot-check the rounded delta appears in the narrative.
    assert f"{change['delta']:.2f}" in body["result"]["explanation"] or "%" not in body["result"]["explanation"]


def test_run_scenario_rejects_empty_allocations(client) -> None:
    headers = _register_and_auth(client, email="empty-allocations@example.com")
    response = client.post(
        "/api/v1/experiments/scenarios", headers=headers, json={"name": "Empty", "allocations": []}
    )
    assert response.status_code == 422


def test_mixed_allocation_scenario_covers_multiple_components(client) -> None:
    headers = _register_and_auth(client, email="mixed-scenario@example.com")
    response = client.post(
        "/api/v1/experiments/scenarios",
        headers=headers,
        json={
            "name": "Mixed SQL and communication plan",
            "allocations": [
                {"skill_name": "SQL", "activity_type": "practice_problems", "hours": 15},
                {"skill_name": "Communication", "activity_type": "mock_interview", "hours": 5},
            ],
        },
    )
    assert response.status_code == 201
    component_types = {c["component_type"] for c in response.json()["result"]["component_changes"]}
    assert component_types == {"technical_readiness", "communication_readiness"}


def test_compare_scenarios_side_by_side(client) -> None:
    headers = _register_and_auth(client, email="compare-scenarios@example.com")

    sql_scenario = client.post(
        "/api/v1/experiments/scenarios",
        headers=headers,
        json={"name": "20h SQL", "allocations": [{"skill_name": "SQL", "activity_type": "practice_problems", "hours": 20}]},
    ).json()
    dsa_scenario = client.post(
        "/api/v1/experiments/scenarios",
        headers=headers,
        json={"name": "20h DSA", "allocations": [{"skill_name": "Data Structures", "activity_type": "practice_problems", "hours": 20}]},
    ).json()
    comm_scenario = client.post(
        "/api/v1/experiments/scenarios",
        headers=headers,
        json={"name": "20h Communication", "allocations": [{"skill_name": "Communication", "activity_type": "mock_interview", "hours": 20}]},
    ).json()

    compare = client.get(
        "/api/v1/experiments/compare",
        headers=headers,
        params={"scenario_ids": [sql_scenario["id"], dsa_scenario["id"], comm_scenario["id"]]},
    )
    assert compare.status_code == 200
    results = compare.json()
    assert len(results) == 3
    names = {r["name"] for r in results}
    assert names == {"20h SQL", "20h DSA", "20h Communication"}
    for r in results:
        assert r["result"]["disclaimer"] == "Personalized scenario estimate—not a guaranteed outcome or hiring prediction."

    listing = client.get("/api/v1/experiments/scenarios", headers=headers)
    assert listing.status_code == 200
    assert len(listing.json()) == 3


def test_cross_student_cannot_access_or_compare_another_students_scenario(client) -> None:
    headers_a = _register_and_auth(client, email="scenario-owner@example.com")
    headers_b = _register_and_auth(client, email="scenario-attacker@example.com")

    scenario = client.post(
        "/api/v1/experiments/scenarios",
        headers=headers_a,
        json={"name": "Private plan", "allocations": [{"skill_name": "SQL", "activity_type": "practice_problems", "hours": 20}]},
    ).json()

    forbidden = client.get(f"/api/v1/experiments/scenarios/{scenario['id']}", headers=headers_b)
    assert forbidden.status_code == 404

    forbidden_compare = client.get(
        "/api/v1/experiments/compare", headers=headers_b, params={"scenario_ids": [scenario["id"]]}
    )
    assert forbidden_compare.status_code == 404

    own_list = client.get("/api/v1/experiments/scenarios", headers=headers_b)
    assert own_list.json() == []
