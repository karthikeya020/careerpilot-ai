"""Career Twin small-sample safeguard (twin-v2): a single session's evidence
must never read as a confidently established skill level. See
docs/implementation/CAREER_TWIN_SCORING.md "Small-sample safeguard" for the
formula this locks in -- evidence-diversity weighting, prior-weighted
(shrinkage) scoring, and a hard confidence cap below the stability
thresholds.
"""

from sqlalchemy import select

from app.career_twin.scoring import (
    HIGH_DISAGREEMENT_THRESHOLD,
    LOW_SAMPLE_CONFIDENCE_CAP,
    LOW_SAMPLE_NOTICE,
    MIN_EVIDENCE_FOR_STABLE_CONFIDENCE,
    MIN_SOURCE_DIVERSITY_TARGET,
    recompute_twin,
)
from app.models.career_twin import COMPONENT_TECHNICAL
from app.models.skill import EVIDENCE_TYPE_INTERVIEW, Skill, SkillEvidence
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole


def _make_student(db_session, email: str) -> StudentProfile:
    role = db_session.scalar(select(Role).where(Role.name == "student"))
    user = User(email=email, password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    profile = StudentProfile(user_id=user.id, full_name="Twin Student")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile


def _add_evidence(
    db_session,
    profile: StudentProfile,
    skill: Skill,
    *,
    normalized_score: float,
    source_object_type: str,
    confidence: float = 0.8,
    weight: float = 0.9,
) -> None:
    db_session.add(
        SkillEvidence(
            student_profile_id=profile.id,
            skill_id=skill.id,
            evidence_type=EVIDENCE_TYPE_INTERVIEW,
            source_object_type=source_object_type,
            raw_score=normalized_score,
            normalized_score=normalized_score,
            weight=weight,
            confidence=confidence,
            explanation="test evidence",
        )
    )
    db_session.commit()


def _technical_component(snapshot):
    return {c.component_type: c for c in snapshot.components}[COMPONENT_TECHNICAL]


def test_one_strong_answer_is_shrunk_and_flagged_low_sample(db_session) -> None:
    """A single 0.95-scoring interview answer must not read as a confidently
    established 90%+ skill level."""
    profile = _make_student(db_session, "one-answer@example.com")
    skill = db_session.scalar(select(Skill).where(Skill.name == "Python"))
    _add_evidence(db_session, profile, skill, normalized_score=0.95, source_object_type="interview_answer")

    snapshot = recompute_twin(db_session, profile, reason="one strong answer")
    technical = _technical_component(snapshot)

    assert technical.evidence_count == 1
    assert technical.evidence_diversity == 1
    assert technical.is_low_sample is True
    # Shrunk well below the raw 0.95 -- never a face-value 90-100% claim from one item.
    assert float(technical.score) < 0.75
    assert float(technical.confidence) <= LOW_SAMPLE_CONFIDENCE_CAP
    assert LOW_SAMPLE_NOTICE in technical.explanation


def test_several_strong_answers_same_source_still_capped_by_diversity(db_session) -> None:
    """Multiple strong items from the SAME source (e.g. one interview
    session) raise volume but must stay diversity-capped -- repetition from
    one source is not the same as independent corroboration."""
    profile = _make_student(db_session, "several-same-source@example.com")
    skill = db_session.scalar(select(Skill).where(Skill.name == "Python"))
    for _ in range(5):
        _add_evidence(db_session, profile, skill, normalized_score=0.9, source_object_type="interview_answer")

    snapshot = recompute_twin(db_session, profile, reason="several strong answers, one source")
    technical = _technical_component(snapshot)

    assert technical.evidence_count == 5
    assert technical.evidence_diversity == 1
    # Full evidence volume alone (5 >= MIN_EVIDENCE_FOR_STABLE_CONFIDENCE) does
    # NOT clear low-sample status, because diversity is still below target.
    assert technical.is_low_sample is True
    assert float(technical.confidence) <= LOW_SAMPLE_CONFIDENCE_CAP
    # Still meaningfully shrunk toward the prior relative to the raw 0.9.
    assert float(technical.score) < 0.85


def test_conflicting_evidence_lowers_confidence_and_is_flagged(db_session) -> None:
    """Evidence that actively disagrees (one very high, one very low score
    for the same component) must reduce confidence further and say so."""
    profile = _make_student(db_session, "conflicting@example.com")
    skill = db_session.scalar(select(Skill).where(Skill.name == "Python"))
    _add_evidence(db_session, profile, skill, normalized_score=0.95, source_object_type="interview_answer")
    _add_evidence(db_session, profile, skill, normalized_score=0.1, source_object_type="resume")

    snapshot = recompute_twin(db_session, profile, reason="conflicting evidence")
    technical = _technical_component(snapshot)

    assert technical.evidence_count == 2
    assert technical.evidence_diversity == 2
    assert "disagrees significantly" in technical.explanation
    # A middling raw average with high internal disagreement should not
    # report meaningfully higher confidence than the single-item case.
    assert float(technical.confidence) <= LOW_SAMPLE_CONFIDENCE_CAP


def test_repeated_evidence_from_only_one_source_stays_below_diversity_target(db_session) -> None:
    """Isolates the diversity dimension: many items, one source, held below
    what independent-source evidence would achieve for the same volume."""
    profile = _make_student(db_session, "one-source-only@example.com")
    skill = db_session.scalar(select(Skill).where(Skill.name == "Python"))
    for _ in range(4):
        _add_evidence(db_session, profile, skill, normalized_score=0.85, source_object_type="interview_answer")

    snapshot = recompute_twin(db_session, profile, reason="repeated evidence, one source")
    technical = _technical_component(snapshot)

    assert technical.evidence_diversity == 1
    assert technical.evidence_count >= MIN_EVIDENCE_FOR_STABLE_CONFIDENCE
    # Volume alone reached the stability threshold, but diversity didn't --
    # still low-sample.
    assert technical.is_low_sample is True


def test_evidence_from_multiple_independent_sources_clears_low_sample(db_session) -> None:
    """The intended graduation path: enough evidence AND enough distinct
    sources reaches a real, non-capped, non-shrunk-to-the-floor estimate."""
    profile = _make_student(db_session, "multi-source@example.com")
    skill = db_session.scalar(select(Skill).where(Skill.name == "Python"))
    _add_evidence(db_session, profile, skill, normalized_score=0.85, source_object_type="interview_answer")
    _add_evidence(db_session, profile, skill, normalized_score=0.85, source_object_type="resume")
    _add_evidence(db_session, profile, skill, normalized_score=0.85, source_object_type="question_response")

    snapshot = recompute_twin(db_session, profile, reason="multi-source evidence")
    technical = _technical_component(snapshot)

    assert technical.evidence_count == 3
    assert technical.evidence_diversity >= MIN_SOURCE_DIVERSITY_TARGET
    assert technical.is_low_sample is False
    assert LOW_SAMPLE_NOTICE not in technical.explanation
    # No internal disagreement (all 0.85) and enough volume+diversity --
    # confidence is allowed to exceed the low-sample cap.
    assert float(technical.confidence) > LOW_SAMPLE_CONFIDENCE_CAP
    # Score should sit close to the raw agreed-upon value, not shrunk to the floor.
    assert float(technical.score) > 0.75


def test_high_disagreement_threshold_constant_is_reasonable() -> None:
    assert 0.0 < HIGH_DISAGREEMENT_THRESHOLD < 1.0
