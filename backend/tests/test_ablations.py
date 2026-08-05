"""All six ablation seams named in the release scope, run for real: CARE
routing (reused from Experiment A), graph/vector retrieval (reused from
Experiment B), and the three newly-harnessed seams -- Career Twin memory,
reflection/critic, and consensus -- each calling the real production agent,
never a hand-computed number. See app/evaluation/ablations.py.
"""

from sqlalchemy import select

from app.evaluation.ablations import (
    run_career_twin_memory_ablation,
    run_consensus_ablation,
    run_full_ablation_suite,
    run_reflection_ablation,
)
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole


def _make_student(db_session, email: str) -> StudentProfile:
    role = db_session.scalar(select(Role).where(Role.name == "student"))
    user = User(email=email, password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, full_name="Ablation Student")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def test_consensus_ablation_penalizes_high_disagreement_more_than_low(db_session):
    report = run_consensus_ablation(db_session)
    assert report["ablation"] == "consensus"
    assert report["case_count"] == 4
    by_case = {row["case_id"]: row for row in report["rows"]}

    low = by_case["low-disagreement"]
    extreme = by_case["extreme-disagreement"]
    # Consensus confidence is never above the raw mean (disagreement only ever penalizes).
    assert low["consensus_confidence"] <= low["raw_mean_confidence"]
    assert extreme["consensus_confidence"] <= extreme["raw_mean_confidence"]
    # The penalty (mean - consensus) grows with disagreement.
    low_penalty = low["raw_mean_confidence"] - low["consensus_confidence"]
    extreme_penalty = extreme["raw_mean_confidence"] - extreme["consensus_confidence"]
    assert extreme_penalty > low_penalty
    assert extreme["flagged_for_escalation"] is True
    assert low["flagged_for_escalation"] is False


def test_reflection_ablation_only_penalizes_uncited_high_confidence_claims(db_session):
    report = run_reflection_ablation(db_session)
    assert report["ablation"] == "reflection"
    by_case = {row["case_id"]: row for row in report["rows"]}

    clean = by_case["clean-grounded-council"]
    assert clean["delta"] == 0.0
    assert clean["verdict"] == "pass"

    two_unsupported = by_case["two-unsupported-high-confidence-claims"]
    one_unsupported = by_case["one-unsupported-high-confidence-claim"]
    assert two_unsupported["delta"] < one_unsupported["delta"] < 0
    assert two_unsupported["verdict"] == "flag"

    low_confidence = by_case["low-confidence-uncited-under-threshold"]
    assert low_confidence["delta"] == 0.0  # below the critic's unsupported-confidence threshold


def test_career_twin_memory_ablation_uses_a_real_student_and_shifts_confidence(db_session):
    profile = _make_student(db_session, "memory-ablation@example.com")
    report = run_career_twin_memory_ablation(db_session, student_profile_id=profile.id)

    assert report["ablation"] == "career_twin_memory"
    assert report["student_profile_used"] == str(profile.id)
    assert report["memory_found"] is not None
    for row in report["rows"]:
        assert "memory_enabled_consensus_confidence" in row
        # Memory's confidence is currently a constant 1.0, so enabling it can only pull
        # the council's consensus confidence up, never down.
        assert row["memory_enabled_consensus_confidence"] >= row["memory_disabled_consensus_confidence"]


def test_career_twin_memory_ablation_handles_no_profile_gracefully(db_session):
    import uuid

    report = run_career_twin_memory_ablation(db_session, student_profile_id=uuid.uuid4())
    assert report["memory_found"] is None
    for row in report["rows"]:
        assert "memory_enabled_consensus_confidence" not in row


def test_full_ablation_suite_reports_all_six_seams(db_session):
    _make_student(db_session, "full-suite-ablation@example.com")
    report = run_full_ablation_suite(db_session)

    assert report["harness_version"] == "ablation-v1"
    seams = report["ablations"]
    assert set(seams.keys()) == {
        "1_care_disabled_vs_enabled",
        "2_graph_retrieval_disabled_vs_enabled",
        "3_vector_retrieval_disabled_vs_enabled",
        "4_career_twin_memory_disabled_vs_enabled",
        "5_reflection_disabled_vs_enabled",
        "6_consensus_disabled_vs_enabled",
    }
    # Every seam must carry a real run_id or case data -- never a placeholder.
    assert seams["1_care_disabled_vs_enabled"]["case_count"] > 0
    assert seams["2_graph_retrieval_disabled_vs_enabled"]["graph_enabled_accuracy"] == 1.0
    assert seams["3_vector_retrieval_disabled_vs_enabled"]["vector_disabled_accuracy"] == 1.0
    assert seams["4_career_twin_memory_disabled_vs_enabled"]["case_count"] > 0
    assert seams["5_reflection_disabled_vs_enabled"]["case_count"] > 0
    assert seams["6_consensus_disabled_vs_enabled"]["case_count"] > 0
