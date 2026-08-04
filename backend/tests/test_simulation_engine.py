"""Career Experiment Lab simulation engine (sim-v1): deterministic,
versioned, and never LLM-computed. See
app/simulation/engine.py and docs/implementation/CAREER_TWIN_SCORING.md-
adjacent EXPERIMENT_LAB_SIMULATION.md for the formula this locks in.
"""

from sqlalchemy import select

from app.career_twin.scoring import recompute_twin
from app.models.career_twin import COMPONENT_COMMUNICATION, COMPONENT_TECHNICAL
from app.models.job_description import REQUIREMENT_SKILL, JobDescription, JobRequirement
from app.models.skill import EVIDENCE_TYPE_INTERVIEW, Skill, SkillEvidence
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole
from app.simulation.engine import (
    DISCLAIMER,
    SIMULATION_ENGINE_VERSION,
    AllocationInput,
    simulate_scenario,
)


def _make_student(db_session, email: str) -> StudentProfile:
    role = db_session.scalar(select(Role).where(Role.name == "student"))
    user = User(email=email, password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, full_name="Sim Student")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def _give_evidence(db_session, profile, skill_name, *, count, sources, score=0.7, confidence=0.75):
    skill = db_session.scalar(select(Skill).where(Skill.name == skill_name))
    for i in range(count):
        db_session.add(
            SkillEvidence(
                student_profile_id=profile.id,
                skill_id=skill.id,
                evidence_type=EVIDENCE_TYPE_INTERVIEW,
                source_object_type=sources[i % len(sources)],
                raw_score=score,
                normalized_score=score,
                weight=0.9,
                confidence=confidence,
                explanation="seed evidence",
            )
        )
    db_session.commit()
    recompute_twin(db_session, profile, reason="seed evidence")


def _component(result, component_type):
    return next(c for c in result.component_changes if c.component_type == component_type)


def test_engine_version_is_stable():
    assert SIMULATION_ENGINE_VERSION == "sim-v1"


def test_disclaimer_is_present_and_exact():
    assert DISCLAIMER == "Personalized scenario estimate—not a guaranteed outcome or hiring prediction."


def test_simulate_with_no_career_twin_yet_uses_neutral_prior(db_session) -> None:
    profile = _make_student(db_session, "no-twin@example.com")

    result = simulate_scenario(db_session, profile, [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=20)])

    assert result.current_overall_score is None
    assert result.baseline_snapshot_id is None
    change = _component(result, COMPONENT_TECHNICAL)
    assert change.current_score is None
    assert 0.5 < change.simulated_score < 0.9
    assert result.disclaimer == DISCLAIMER


def test_unresolved_skill_produces_no_effect_and_an_assumption_note(db_session) -> None:
    profile = _make_student(db_session, "unresolved-skill@example.com")

    result = simulate_scenario(
        db_session, profile, [AllocationInput(skill_name="Not A Real Skill", activity_type="practice_problems", hours=20)]
    )

    assert result.component_changes == []
    assert any("not recognized" in a for a in result.assumptions)


def test_more_hours_yields_more_gain_but_with_diminishing_returns(db_session) -> None:
    profile_a = _make_student(db_session, "few-hours@example.com")
    profile_b = _make_student(db_session, "many-hours@example.com")

    result_5h = simulate_scenario(db_session, profile_a, [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=5)])
    result_40h = simulate_scenario(db_session, profile_b, [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=40)])
    result_200h = simulate_scenario(
        db_session, profile_b, [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=200)]
    )

    gain_5h = _component(result_5h, COMPONENT_TECHNICAL).delta
    gain_40h = _component(result_40h, COMPONENT_TECHNICAL).delta
    gain_200h = _component(result_200h, COMPONENT_TECHNICAL).delta

    assert 0 < gain_5h < gain_40h < gain_200h
    # Diminishing returns: doubling far past saturation adds much less than
    # the initial jump did.
    assert (gain_200h - gain_40h) < (gain_40h - gain_5h)


def test_job_description_requirement_increases_simulated_gain(db_session) -> None:
    profile_no_jd = _make_student(db_session, "no-jd@example.com")
    profile_with_jd = _make_student(db_session, "with-jd@example.com")

    sql_skill = db_session.scalar(select(Skill).where(Skill.name == "SQL"))
    jd = JobDescription(
        student_profile_id=profile_with_jd.id, title="Data Analyst", raw_text="Requires strong SQL skills.", source="pasted"
    )
    db_session.add(jd)
    db_session.flush()
    db_session.add(
        JobRequirement(
            job_description_id=jd.id, requirement_type=REQUIREMENT_SKILL, skill_id=sql_skill.id, raw_text="SQL", is_required=True
        )
    )
    db_session.commit()

    allocation = [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=20)]
    result_no_jd = simulate_scenario(db_session, profile_no_jd, allocation)
    result_with_jd = simulate_scenario(db_session, profile_with_jd, allocation)

    assert _component(result_with_jd, COMPONENT_TECHNICAL).delta > _component(result_no_jd, COMPONENT_TECHNICAL).delta
    assert any("job description" in a.lower() for a in result_with_jd.assumptions)


def test_positive_historical_trend_boosts_projected_gain(db_session) -> None:
    profile_flat = _make_student(db_session, "flat-history@example.com")
    profile_trending = _make_student(db_session, "trending-history@example.com")

    # Two snapshots with a clearly rising Technical trend for profile_trending.
    _give_evidence(db_session, profile_trending, "SQL", count=1, sources=["resume"], score=0.4)
    _give_evidence(db_session, profile_trending, "SQL", count=3, sources=["resume", "interview_answer"], score=0.9)
    _give_evidence(db_session, profile_flat, "SQL", count=1, sources=["resume"], score=0.5)

    allocation = [AllocationInput(skill_name="Python", activity_type="practice_problems", hours=20)]
    result_flat = simulate_scenario(db_session, profile_flat, allocation)
    result_trending = simulate_scenario(db_session, profile_trending, allocation)

    assert _component(result_trending, COMPONENT_TECHNICAL).delta > _component(result_flat, COMPONENT_TECHNICAL).delta
    assert any("historical" in a.lower() for a in result_trending.assumptions)


def test_mixed_allocations_affect_independent_components(db_session) -> None:
    profile = _make_student(db_session, "mixed-alloc@example.com")

    result = simulate_scenario(
        db_session,
        profile,
        [
            AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=20),
            AllocationInput(skill_name="Communication", activity_type="mock_interview", hours=10),
        ],
    )

    types = {c.component_type for c in result.component_changes}
    assert types == {COMPONENT_TECHNICAL, COMPONENT_COMMUNICATION}
    assert all(c.delta > 0 for c in result.component_changes)


def test_two_allocations_same_component_show_within_scenario_diminishing_returns(db_session) -> None:
    profile_one = _make_student(db_session, "one-allocation@example.com")
    profile_two = _make_student(db_session, "two-allocations@example.com")

    result_one = simulate_scenario(db_session, profile_one, [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=20)])
    result_two = simulate_scenario(
        db_session,
        profile_two,
        [
            AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=20),
            AllocationInput(skill_name="Python", activity_type="practice_problems", hours=20),
        ],
    )

    gain_one = _component(result_one, COMPONENT_TECHNICAL).delta
    gain_two = _component(result_two, COMPONENT_TECHNICAL).delta
    # The second allocation to the same (Technical) component starts from a
    # higher running base, so it contributes less headroom-adjusted gain than
    # if it were the only allocation -- total gain is sub-additive, not double.
    assert gain_one < gain_two < gain_one * 2


def test_confidence_and_uncertainty_are_complementary(db_session) -> None:
    profile = _make_student(db_session, "confidence-check@example.com")

    result = simulate_scenario(db_session, profile, [AllocationInput(skill_name="SQL", activity_type="practice_problems", hours=20)])
    change = _component(result, COMPONENT_TECHNICAL)
    assert round(change.confidence + change.uncertainty, 4) == 1.0
    assert round(result.overall_confidence + result.overall_uncertainty, 4) == 1.0
