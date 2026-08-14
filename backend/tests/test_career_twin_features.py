"""Career Twin feature-expansion tests: evidence freshness/decay,
ripple-effect cross-component notes, time-to-target projection, multi-role
alignment, evidence provenance breakdown, milestone moments, and the
shareable snapshot proof export."""

from datetime import timedelta

from sqlalchemy import select

from app.career_twin.multi_role import score_multi_role_alignment
from app.career_twin.projection import project_time_to_target
from app.career_twin.proof import build_snapshot_proof
from app.career_twin.scoring import build_career_twin_snapshot_out, recompute_twin
from app.models.base import utcnow
from app.models.career_twin import COMPONENT_ROLE_ALIGNMENT, COMPONENT_TECHNICAL
from app.models.skill import (
    EVIDENCE_TYPE_ASSESSMENT,
    EVIDENCE_TYPE_JOB_MATCH,
    EVIDENCE_TYPE_PROJECT,
    EVIDENCE_TYPE_RESUME,
    EVIDENCE_TYPE_SELF_ASSESSMENT,
    Skill,
    SkillEvidence,
)
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole


def _make_student(db_session, email="twin-features@example.com") -> StudentProfile:
    role = db_session.scalar(select(Role).where(Role.name == "student"))
    user = User(email=email, password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, full_name="Twin Features Student")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def _add_evidence(db_session, profile, skill_name, evidence_type, source_object_type, *, score=0.9, weight=0.9, confidence=0.8, age_days=0):
    skill = db_session.scalar(select(Skill).where(Skill.name == skill_name))
    assert skill is not None, f"unknown skill {skill_name!r}"
    evidence = SkillEvidence(
        student_profile_id=profile.id,
        skill_id=skill.id,
        evidence_type=evidence_type,
        source_object_type=source_object_type,
        source_object_id=None,
        raw_score=score,
        normalized_score=score,
        weight=weight,
        confidence=confidence,
        explanation=f"Evidence for {skill_name}.",
    )
    db_session.add(evidence)
    db_session.flush()
    if age_days:
        evidence.created_at = utcnow() - timedelta(days=age_days)
    db_session.commit()
    return evidence


class TestEvidenceFreshness:
    def test_majority_stale_evidence_caps_confidence_with_notice(self, db_session):
        profile = _make_student(db_session, "freshness-stale@example.com")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_SELF_ASSESSMENT, "student_profile", age_days=250)
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_ASSESSMENT, "assessment_attempt", age_days=220)
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_RESUME, "resume", age_days=1)

        snapshot = recompute_twin(db_session, profile, reason="freshness test")
        out = build_career_twin_snapshot_out(db_session, snapshot)
        technical = next(c for c in out.components if c.component_type == COMPONENT_TECHNICAL)

        assert technical.is_low_sample is False
        assert technical.is_stale_evidence is True
        assert technical.confidence <= 0.60
        assert technical.stale_evidence_fraction > 0.5
        assert "6+ months old" in technical.stale_evidence_notice

    def test_fresh_evidence_is_not_flagged_stale(self, db_session):
        profile = _make_student(db_session, "freshness-fresh@example.com")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_SELF_ASSESSMENT, "student_profile", age_days=0)
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_ASSESSMENT, "assessment_attempt", age_days=1)
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_RESUME, "resume", age_days=2)

        snapshot = recompute_twin(db_session, profile, reason="freshness test")
        out = build_career_twin_snapshot_out(db_session, snapshot)
        technical = next(c for c in out.components if c.component_type == COMPONENT_TECHNICAL)

        assert technical.is_stale_evidence is False
        assert technical.stale_evidence_notice is None


class TestRippleAndProvenance:
    def test_shared_skill_across_components_produces_a_ripple_note(self, db_session):
        profile = _make_student(db_session, "ripple@example.com")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_PROJECT, "resume")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_JOB_MATCH, "job_description")

        snapshot = recompute_twin(db_session, profile, reason="ripple test")
        out = build_career_twin_snapshot_out(db_session, snapshot)
        technical = next(c for c in out.components if c.component_type == COMPONENT_TECHNICAL)

        targets = {n.target_component for n in technical.ripple_notes}
        assert COMPONENT_ROLE_ALIGNMENT in targets

    def test_provenance_breakdown_sums_to_roughly_one(self, db_session):
        profile = _make_student(db_session, "provenance@example.com")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_SELF_ASSESSMENT, "student_profile", weight=0.6)
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_ASSESSMENT, "assessment_attempt", weight=0.4)

        snapshot = recompute_twin(db_session, profile, reason="provenance test")
        out = build_career_twin_snapshot_out(db_session, snapshot)
        technical = next(c for c in out.components if c.component_type == COMPONENT_TECHNICAL)

        assert set(technical.provenance.keys()) == {EVIDENCE_TYPE_SELF_ASSESSMENT, EVIDENCE_TYPE_ASSESSMENT}
        assert abs(sum(technical.provenance.values()) - 1.0) < 0.01


class TestMilestones:
    def test_component_crossing_threshold_for_the_first_time_is_a_milestone(self, db_session):
        profile = _make_student(db_session, "milestone@example.com")
        for src in ["student_profile", "assessment_attempt", "resume"]:
            _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_ASSESSMENT if src == "assessment_attempt" else (
                EVIDENCE_TYPE_RESUME if src == "resume" else EVIDENCE_TYPE_SELF_ASSESSMENT
            ), src, score=0.95, weight=0.95, confidence=0.9)

        snapshot = recompute_twin(db_session, profile, reason="milestone test")
        out = build_career_twin_snapshot_out(db_session, snapshot)
        technical = next(c for c in out.components if c.component_type == COMPONENT_TECHNICAL)

        assert technical.score is not None and technical.score >= 0.70
        assert any("Technical" in m and "70%" in m for m in out.milestones)

        second = recompute_twin(db_session, profile, reason="second pass, no new evidence")
        second_out = build_career_twin_snapshot_out(db_session, second)
        assert not any("Technical" in m and "70%" in m for m in second_out.milestones)

    def test_insufficient_evidence_resolving_is_a_milestone(self, db_session):
        profile = _make_student(db_session, "milestone-resolve@example.com")
        first = recompute_twin(db_session, profile, reason="no evidence yet")
        first_out = build_career_twin_snapshot_out(db_session, first)
        assert first_out.milestones == []

        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_SELF_ASSESSMENT, "student_profile")
        second = recompute_twin(db_session, profile, reason="first evidence")
        second_out = build_career_twin_snapshot_out(db_session, second)
        assert any("enough evidence to be scored" in m for m in second_out.milestones)


class TestTimeToTargetProjection:
    def test_no_history_is_insufficient(self, db_session):
        profile = _make_student(db_session, "projection-none@example.com")
        projections = project_time_to_target(db_session, profile.id)
        technical = next(p for p in projections if p.component_type == COMPONENT_TECHNICAL)
        assert technical.status == "insufficient_history"

    def test_improving_trend_projects_a_positive_weeks_estimate(self, db_session):
        profile = _make_student(db_session, "projection-improving@example.com")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_SELF_ASSESSMENT, "student_profile", score=0.3, weight=0.3, confidence=0.3)
        first = recompute_twin(db_session, profile, reason="baseline")
        first.created_at = utcnow() - timedelta(weeks=6)
        db_session.commit()

        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_ASSESSMENT, "assessment_attempt", score=0.6, weight=0.6, confidence=0.6)
        second = recompute_twin(db_session, profile, reason="improved")

        projections = project_time_to_target(db_session, profile.id)
        technical = next(p for p in projections if p.component_type == COMPONENT_TECHNICAL)
        assert technical.status == "projected"
        assert technical.weeks_to_target is not None
        assert technical.weeks_to_target > 0
        assert "not a guarantee" in technical.note.lower() or "heuristic" in technical.note.lower()


class TestMultiRoleAlignment:
    def test_different_roles_produce_different_alignment_and_are_sorted(self, db_session):
        profile = _make_student(db_session, "multirole@example.com")
        _add_evidence(db_session, profile, "SQL", EVIDENCE_TYPE_PROJECT, "resume", weight=0.9)
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_PROJECT, "resume", weight=0.9)
        _add_evidence(db_session, profile, "Data Analysis", EVIDENCE_TYPE_PROJECT, "resume", weight=0.9)
        _add_evidence(db_session, profile, "Pandas", EVIDENCE_TYPE_PROJECT, "resume", weight=0.9)

        results = score_multi_role_alignment(db_session, profile.id)
        by_role = {r.role_title: r.alignment for r in results}

        assert by_role["Data Analyst"] > by_role["Frontend Engineer"]
        assert results == sorted(results, key=lambda r: r.alignment, reverse=True)


class TestSnapshotProof:
    def test_proof_resolves_citations_and_carries_a_disclaimer(self, db_session):
        profile = _make_student(db_session, "proof@example.com")
        _add_evidence(db_session, profile, "Python", EVIDENCE_TYPE_SELF_ASSESSMENT, "student_profile")
        snapshot = recompute_twin(db_session, profile, reason="proof test")

        proof = build_snapshot_proof(db_session, profile, snapshot)

        assert proof.student_name == "Twin Features Student"
        assert "not a hiring recommendation" in proof.disclaimer.lower()
        technical = next(c for c in proof.components if c.component_type == COMPONENT_TECHNICAL)
        assert any(cite.skill_name == "Python" for cite in technical.citations)
