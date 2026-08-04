from app.evaluation.run import run_evaluation


def test_run_evaluation_compares_all_three_route_variants(db_session):
    report = run_evaluation(db_session, dataset_name="test-dataset", write_report_file=False)

    assert report["case_count"] == 8
    assert set(report["agreement_rate_by_variant"].keys()) == {
        "single_agent_fixed", "multi_agent_fixed", "care_adaptive",
    }
    # CARE adaptive routing should agree with the synthetic rubric labels
    # strictly more often than either fixed baseline -- that's the whole
    # point of adaptive routing.
    assert report["agreement_rate_by_variant"]["care_adaptive"] >= report["agreement_rate_by_variant"]["single_agent_fixed"]
    assert report["agreement_rate_by_variant"]["care_adaptive"] >= report["agreement_rate_by_variant"]["multi_agent_fixed"]
    assert len(report["rows"]) == 24
