"""Research Benchmark Lab: routing-strategy comparison (Experiment A),
GraphRAG-vs-vector-only retrieval comparison (Experiment B), and confidence
calibration -- all computed from real runs against real code paths, never
invented values.
"""


def _register_and_auth(client, email="research-lab@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Research Lab Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_routing_experiment_produces_real_agreement_rates(client) -> None:
    headers = _register_and_auth(client)
    response = client.post("/api/v1/research/experiments/routing", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["case_count"] > 0
    assert set(body["agreement_rate_by_variant"].keys()) == {"single_agent_fixed", "multi_agent_fixed", "care_adaptive"}
    for rate in body["agreement_rate_by_variant"].values():
        assert 0.0 <= rate <= 1.0
    # CARE adaptive routing is designed to track the rubric labels best of the three.
    assert body["agreement_rate_by_variant"]["care_adaptive"] >= body["agreement_rate_by_variant"]["single_agent_fixed"]


def test_graph_vs_vector_experiment_is_real_and_labeled_preliminary(client) -> None:
    headers = _register_and_auth(client, email="graph-vs-vector@example.com")
    response = client.post("/api/v1/research/experiments/graph-vs-vector", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["case_count"] > 0
    assert body["graph_traversal_accuracy"] == 1.0
    assert body["vector_only_accuracy"] is not None
    assert 0.0 <= body["vector_only_accuracy"] <= 1.0
    assert "preliminary" in body["sample_size_warning"].lower()
    assert "construction" in body["methodology_note"].lower()


def test_list_runs_includes_both_experiments(client) -> None:
    headers = _register_and_auth(client, email="list-runs@example.com")
    client.post("/api/v1/research/experiments/routing", headers=headers)
    client.post("/api/v1/research/experiments/graph-vs-vector", headers=headers)

    response = client.get("/api/v1/research/runs", headers=headers)
    assert response.status_code == 200
    names = {r["name"] for r in response.json()}
    assert "CARE routing comparison" in names
    assert "GraphRAG traversal vs vector-only retrieval" in names
    for run in response.json():
        assert run["result_count"] > 0


def test_calibration_report_reflects_real_stored_results(client) -> None:
    headers = _register_and_auth(client, email="calibration@example.com")
    client.post("/api/v1/research/experiments/routing", headers=headers)

    response = client.get("/api/v1/research/calibration", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["sample_size"] > 0
    assert body["brier_score"] is not None
    assert 0.0 <= body["brier_score"] <= 1.0
    assert body["expected_calibration_error"] is not None
    assert len(body["bins"]) == 5
    assert body["preliminary"] is True  # small curated dataset, honestly labeled


def test_calibration_with_no_data_returns_empty_not_fabricated(client) -> None:
    headers = _register_and_auth(client, email="no-data-calibration@example.com")
    response = client.get("/api/v1/research/calibration", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["sample_size"] == 0
    assert body["brier_score"] is None
    assert body["bins"] == []


def test_research_endpoints_require_auth(client) -> None:
    assert client.post("/api/v1/research/experiments/routing").status_code == 401
    assert client.get("/api/v1/research/runs").status_code == 401
