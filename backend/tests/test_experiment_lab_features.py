"""Experiment Lab feature-expansion tests: inverse-mode target solving,
graph-aware prerequisite ordering, the diminishing-returns curve,
deadline/weekly-budget calendar shaping, opportunity-cost framing,
sensitivity analysis, and the prediction-accuracy bridge to Research Lab."""

from datetime import date, timedelta

from sqlalchemy import select

from app.career_twin.scoring import recompute_twin
from app.models.career_twin import COMPONENT_TECHNICAL
from app.models.skill import EVIDENCE_TYPE_INTERVIEW, Skill, SkillEvidence
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole
from app.services import experiment_service
from app.simulation.engine import ComponentChange, compute_opportunity_cost_notes, compute_sensitivity, simulate_scenario, AllocationInput
from app.simulation.inverse import AllocationPlanItem, build_calendar_plan, marginal_gain_curve, reorder_by_prerequisites, solve_for_target


def _make_student(db_session, email: str) -> StudentProfile:
    role = db_session.scalar(select(Role).where(Role.name == "student"))
    user = User(email=email, password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, full_name="Inverse Student")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def _give_evidence(db_session, profile, skill_name, *, count, sources, score=0.5, confidence=0.6):
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


class TestInverseSolver:
    def test_reaches_a_modest_reachable_target(self, db_session):
        profile = _make_student(db_session, "inverse-reach@example.com")
        _give_evidence(db_session, profile, "Python", count=2, sources=["interview", "resume"])

        result = solve_for_target(
            db_session, profile, COMPONENT_TECHNICAL, target_score=0.55, candidate_skill_names=["Python"], weekly_hours=10
        )
        assert result.reached_target is True
        assert result.total_hours > 0
        assert len(result.plan) >= 1
        assert result.plan[0].skill_name == "Python"

    def test_honestly_reports_infeasibility_for_an_unreachable_target(self, db_session):
        profile = _make_student(db_session, "inverse-infeasible@example.com")

        result = solve_for_target(
            db_session, profile, COMPONENT_TECHNICAL, target_score=0.999, candidate_skill_names=["Python"], weekly_hours=10
        )
        assert result.reached_target is False
        assert any("not reached" in a.lower() for a in result.assumptions)

    def test_unrecognized_skills_produce_no_plan_not_a_fabricated_one(self, db_session):
        profile = _make_student(db_session, "inverse-unknown@example.com")
        result = solve_for_target(
            db_session, profile, COMPONENT_TECHNICAL, target_score=0.6, candidate_skill_names=["Not A Real Skill"], weekly_hours=10
        )
        assert result.plan == []
        assert result.reached_target is False


class TestPrerequisiteReordering:
    def test_frontloads_a_real_cross_skill_prerequisite(self, db_session):
        # Data Structures' "Arrays & Strings" concept DEPENDS_ON Algorithms'
        # "Complexity" concept (app/seed/assessment_taxonomy.py
        # NEW_CONCEPT_DEPENDENCIES) -- a real cross-skill edge.
        plan = [
            AllocationPlanItem(skill_name="Data Structures", activity_type="practice_problems", hours=10, order_rank=1),
            AllocationPlanItem(skill_name="Algorithms", activity_type="practice_problems", hours=4, order_rank=2),
        ]
        reordered = reorder_by_prerequisites(db_session, plan)

        algorithms_item = next(i for i in reordered if i.skill_name == "Algorithms")
        data_structures_item = next(i for i in reordered if i.skill_name == "Data Structures")
        assert algorithms_item.order_rank < data_structures_item.order_rank
        assert algorithms_item.scheduling_reason is not None
        assert "Data Structures" in algorithms_item.scheduling_reason

    def test_no_dependency_between_candidates_keeps_original_hour_ordering(self, db_session):
        plan = [
            AllocationPlanItem(skill_name="Communication", activity_type="mock_interview", hours=4, order_rank=1),
            AllocationPlanItem(skill_name="Python", activity_type="practice_problems", hours=10, order_rank=2),
        ]
        reordered = reorder_by_prerequisites(db_session, plan)
        assert reordered[0].skill_name == "Python"  # larger hours, no prerequisite signal either way
        assert all(item.scheduling_reason is None for item in reordered)


class TestMarginalGainCurve:
    def test_curve_is_diminishing(self):
        points = marginal_gain_curve(activity_type="practice_problems", max_hours=40, step=2)
        assert len(points) > 5
        for i in range(1, len(points)):
            assert points[i].marginal_gain <= points[i - 1].marginal_gain + 1e-9


class TestCalendarPlan:
    def test_respects_weekly_hours_budget(self):
        plan = [
            AllocationPlanItem(skill_name="Python", activity_type="practice_problems", hours=15, order_rank=1),
            AllocationPlanItem(skill_name="SQL", activity_type="practice_problems", hours=10, order_rank=2),
        ]
        calendar = build_calendar_plan(plan, weekly_hours=10)
        assert calendar.total_hours == 25
        assert calendar.weeks_needed == 3
        assert all(week.total_hours <= 10 + 1e-6 for week in calendar.weeks)

    def test_flags_infeasible_deadline(self):
        plan = [AllocationPlanItem(skill_name="Python", activity_type="practice_problems", hours=40, order_rank=1)]
        calendar = build_calendar_plan(plan, weekly_hours=5, start=date(2026, 1, 1), deadline=date(2026, 1, 15))
        assert calendar.fits_deadline is False
        assert calendar.feasibility_note is not None


class TestOpportunityCost:
    def test_flags_hours_spent_on_an_already_strong_component(self):
        changes = [
            ComponentChange(
                component_type="technical_readiness", current_score=0.9, simulated_score=0.93, delta=0.03,
                confidence=0.7, uncertainty=0.3,
            ),
            ComponentChange(
                component_type="communication_readiness", current_score=0.3, simulated_score=0.5, delta=0.2,
                confidence=0.5, uncertainty=0.5,
            ),
        ]
        notes = compute_opportunity_cost_notes(changes)
        assert len(notes) == 1
        assert "technical" in notes[0].lower()
        assert "90%" in notes[0]

    def test_no_notes_when_nothing_is_already_strong(self):
        changes = [
            ComponentChange(
                component_type="technical_readiness", current_score=0.4, simulated_score=0.5, delta=0.1,
                confidence=0.5, uncertainty=0.5,
            )
        ]
        assert compute_opportunity_cost_notes(changes) == []


class TestSensitivityAnalysis:
    def test_picks_a_real_most_fragile_factor(self, db_session):
        profile = _make_student(db_session, "sensitivity@example.com")
        _give_evidence(db_session, profile, "Python", count=2, sources=["interview", "resume"])
        allocations = [AllocationInput(skill_name="Python", activity_type="practice_problems", hours=20)]

        baseline = simulate_scenario(db_session, profile, allocations)
        sensitivity = compute_sensitivity(db_session, profile, allocations, None, baseline)

        assert len(sensitivity) == 4
        assert sensitivity == sorted(sensitivity, key=lambda s: -s.swing)
        assert all(s.swing >= 0 for s in sensitivity)


class TestPredictionAccuracy:
    def test_no_new_evidence_yet_is_reported_honestly(self, db_session):
        profile = _make_student(db_session, "prediction-none@example.com")
        _give_evidence(db_session, profile, "Python", count=1, sources=["interview"])
        scenario = experiment_service.run_scenario(
            db_session, profile, "Test scenario", [{"skill_name": "Python", "activity_type": "practice_problems", "hours": 10}]
        )

        accuracy = experiment_service.evaluate_prediction_accuracy(db_session, profile, scenario.id)
        assert accuracy.status == "no_new_evidence_yet"

    def test_measures_real_predicted_vs_actual_delta_once_evidence_arrives(self, db_session):
        profile = _make_student(db_session, "prediction-measured@example.com")
        _give_evidence(db_session, profile, "Python", count=1, sources=["interview"])
        scenario = experiment_service.run_scenario(
            db_session, profile, "Test scenario", [{"skill_name": "Python", "activity_type": "practice_problems", "hours": 10}]
        )

        _give_evidence(db_session, profile, "SQL", count=3, sources=["interview", "resume", "assessment"], score=0.9, confidence=0.9)

        accuracy = experiment_service.evaluate_prediction_accuracy(db_session, profile, scenario.id)
        assert accuracy.status == "measured"
        assert accuracy.predicted_delta is not None
        assert accuracy.actual_delta is not None
        assert accuracy.absolute_error is not None
        assert accuracy.absolute_error == round(abs(accuracy.predicted_delta - accuracy.actual_delta), 4)
