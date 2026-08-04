from sqlalchemy import select

from app.career_twin.scoring import SCORING_RULE_VERSION, recompute_twin
from app.models.career_twin import (
    COMPONENT_ASSESSMENT,
    COMPONENT_TECHNICAL,
    STATUS_INSUFFICIENT_EVIDENCE,
)
from app.models.skill import EVIDENCE_TYPE_SELF_ASSESSMENT, Skill, SkillEvidence
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole


def _make_student(db_session):
    role = db_session.scalar(select(Role).where(Role.name == "student"))
    user = User(email="twin@example.com", password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, full_name="Twin Student")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def test_recompute_twin_with_no_evidence_is_all_insufficient(db_session) -> None:
    profile = _make_student(db_session)

    snapshot = recompute_twin(db_session, profile, reason="initial")

    assert snapshot.version == 1
    assert snapshot.overall_score is None
    assert snapshot.formula_version == SCORING_RULE_VERSION
    assert {c.component_type: c.status for c in snapshot.components}[COMPONENT_ASSESSMENT] == (
        STATUS_INSUFFICIENT_EVIDENCE
    )
    assert all(c.status == STATUS_INSUFFICIENT_EVIDENCE for c in snapshot.components)


def test_recompute_twin_scores_component_with_evidence_and_versions_up(db_session) -> None:
    profile = _make_student(db_session)
    python_skill = db_session.scalar(select(Skill).where(Skill.name == "Python"))

    db_session.add(
        SkillEvidence(
            student_profile_id=profile.id,
            skill_id=python_skill.id,
            evidence_type=EVIDENCE_TYPE_SELF_ASSESSMENT,
            source_object_type="student_profile",
            source_object_id=profile.id,
            raw_score=0.8,
            normalized_score=0.8,
            weight=0.5,
            confidence=0.4,
            explanation="test evidence",
        )
    )
    db_session.commit()

    first = recompute_twin(db_session, profile, reason="first pass")
    technical = {c.component_type: c for c in first.components}[COMPONENT_TECHNICAL]
    assert technical.status == "scored"
    assert float(technical.score) == 0.8
    assert technical.evidence_count == 1
    # single low-weight/confidence item -> well below full confidence
    assert 0 < float(technical.confidence) < 0.4

    second = recompute_twin(db_session, profile, reason="second pass, no new evidence")
    assert second.version == 2
    assert second.previous_snapshot_id == first.id
    assert float(second.score_delta) == 0.0
