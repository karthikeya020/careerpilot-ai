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


def test_ablation_suite_endpoint_reports_all_six_seams(client) -> None:
    headers = _register_and_auth(client, email="ablation-suite@example.com")
    response = client.post("/api/v1/research/experiments/ablations", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["harness_version"] == "ablation-v1"
    assert len(body["ablations"]) == 6
    assert client.post("/api/v1/research/experiments/ablations").status_code == 401


def test_efficiency_frontier_reports_real_latency_for_all_three_conditions(client) -> None:
    headers = _register_and_auth(client, email="efficiency-frontier@example.com")
    response = client.post("/api/v1/research/experiments/efficiency-frontier", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["case_count"] == 4
    conditions = {row["condition"] for row in body["frontier"]}
    assert conditions == {"single_agent_fixed", "multi_agent_fixed", "care_adaptive"}
    for row in body["frontier"]:
        assert row["mean_latency_ms"] >= 0
        assert row["mean_llm_calls"] >= 1
        assert 0.0 <= row["accuracy"] <= 1.0
    assert "no live api key" in body["cost_note"].lower() or "$0" in body["cost_note"]
    assert client.post("/api/v1/research/experiments/efficiency-frontier").status_code == 401


def test_threshold_tuning_sweeps_and_reports_current_defaults(client) -> None:
    headers = _register_and_auth(client, email="threshold-tuning@example.com")
    response = client.post("/api/v1/research/experiments/threshold-tuning", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["combinations_swept"] > 0
    assert body["current_defaults"]["single_agent_threshold"] == 0.80
    assert 0.0 <= body["current_defaults"]["agreement_rate"] <= 1.0
    assert body["empirical_best"] is not None
    assert body["current_defaults_tied_for_best"] is True  # documented defaults already tie for optimal on this rubric


def test_adversarial_suite_runs_real_agents_against_hostile_inputs(client) -> None:
    headers = _register_and_auth(client, email="adversarial-suite@example.com")
    response = client.post("/api/v1/research/experiments/adversarial", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["case_count"] == 5
    case_ids = {c["case_id"] for c in body["cases"]}
    assert "prompt-injection-in-resume" in case_ids
    assert "prompt-injection-in-answer" in case_ids
    injection_case = next(c for c in body["cases"] if c["case_id"] == "prompt-injection-in-resume")
    assert injection_case["passed"] is True
    assert injection_case["classification"] != "supported"


def test_fallback_fidelity_honestly_reports_not_measurable_without_a_live_key(client) -> None:
    headers = _register_and_auth(client, email="fallback-fidelity@example.com")
    response = client.post("/api/v1/research/experiments/fallback-fidelity", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["measurable"] is False
    assert "no live provider key" in body["message"].lower()


def test_fairness_probe_measures_real_phrasing_sensitivity(client) -> None:
    headers = _register_and_auth(client, email="fairness-probe@example.com")
    response = client.post("/api/v1/research/experiments/fairness-probe", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["pair_count"] == 2
    assert "not a claim" in body["disclaimer"].lower() or "not bias-free" in body["disclaimer"].lower() or "bias-free" in body["disclaimer"].lower()
    assert "identity" in body["disclaimer"].lower()


def test_drift_canary_compares_against_a_frozen_baseline(client) -> None:
    headers = _register_and_auth(client, email="drift-canary@example.com")
    response = client.post("/api/v1/research/experiments/drift-canary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["case_count"] == 3
    assert body["any_drifted"] is False
    for case in body["cases"]:
        assert abs(case["confidence_drift"]) <= body["tolerance"]


def test_live_critic_toggle_shows_a_real_confidence_delta_for_typed_input(client) -> None:
    headers = _register_and_auth(client, email="live-critic-toggle@example.com")
    response = client.post(
        "/api/v1/research/experiments/live-critic-toggle",
        headers=headers,
        json={"transcript": "Indexes are good."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["critic_off_confidence"] != body["critic_on_confidence"]
    assert body["delta"] == round(body["critic_on_confidence"] - body["critic_off_confidence"], 4)
    assert client.post("/api/v1/research/experiments/live-critic-toggle", json={"transcript": "x"}).status_code == 401


def test_research_report_bundles_every_section(client) -> None:
    headers = _register_and_auth(client, email="research-report@example.com")
    response = client.get("/api/v1/research/report", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["report_version"] == "research-report-v1"
    for section in (
        "calibration", "ablations", "efficiency_frontier", "threshold_tuning",
        "adversarial_suite", "fallback_fidelity", "fairness_probe", "drift_canary",
    ):
        assert section in body and body[section] is not None
    assert client.get("/api/v1/research/report").status_code == 401
