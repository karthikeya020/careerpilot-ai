"""Job Match catalog service tests: guaranteed-10 search padding, resume-
evidence-based readiness scoring (the same weighting as JD matching), the
5-job tracked-list cap, and the Job Gap Simulator's honesty."""

from sqlalchemy import select

from app.core.errors import ConflictError, NotFoundError
from app.models.job_catalog import CompanyJobListing
from app.models.skill import EVIDENCE_TYPE_RESUME, Skill, SkillEvidence
from app.models.student import StudentProfile
from app.services import job_catalog_service
from app.services.auth_service import register_student

import pytest


def _make_profile(db_session, email="jobmatch@example.com") -> StudentProfile:
    user = register_student(db_session, email=email, password="Password1", full_name="Job Match Student")
    return db_session.scalar(select(StudentProfile).where(StudentProfile.user_id == user.id))


def _give_resume_evidence(db_session, profile, skill_name: str, weight: float) -> None:
    skill = db_session.scalar(select(Skill).where(Skill.name == skill_name))
    assert skill is not None, f"unknown skill {skill_name!r}"
    db_session.add(
        SkillEvidence(
            student_profile_id=profile.id, skill_id=skill.id, evidence_type=EVIDENCE_TYPE_RESUME,
            source_object_type="resume", source_object_id=None, raw_score=weight, normalized_score=weight,
            weight=weight, confidence=0.8, explanation=f"Detected '{skill_name}' on the uploaded resume.",
        )
    )
    db_session.commit()


def test_search_always_pads_to_ten_results_even_for_a_specific_company(db_session):
    profile = _make_profile(db_session, "search-pad@example.com")
    results = job_catalog_service.search_listings(db_session, profile, company_query="Google")
    assert len(results) == 10
    assert results[0].listing.company == "Google"
    # The other nine are real, distinct, same-sector-caliber listings, not padding duplicates.
    assert len({r.listing.id for r in results}) == 10
    assert all(r.listing.sector == "faang" for r in results)


def test_sector_filter_returns_exactly_that_sectors_ten_listings(db_session):
    profile = _make_profile(db_session, "search-sector@example.com")
    results = job_catalog_service.search_listings(db_session, profile, sector="government")
    assert len(results) == 10
    assert all(r.listing.sector == "government" for r in results)


def test_package_tier_filter_excludes_lower_paying_roles(db_session):
    profile = _make_profile(db_session, "search-package@example.com")
    results = job_catalog_service.search_listings(db_session, profile, package_tier="30")
    assert len(results) > 0
    assert all(float(r.listing.package_max_lpa) >= 30 for r in results)


def test_readiness_reflects_real_resume_evidence(db_session):
    profile = _make_profile(db_session, "readiness@example.com")
    listing = db_session.scalar(select(CompanyJobListing).where(CompanyJobListing.company == "Google"))
    assert listing is not None

    required_count = len([r for r in listing.requirements if r.is_required])
    before = job_catalog_service.get_listing_match(db_session, profile, listing.id)
    assert before.readiness is not None
    assert len(before.missing_skills) == required_count

    for skill_name in ["Data Structures", "Algorithms", "Python"]:
        _give_resume_evidence(db_session, profile, skill_name, weight=0.95)

    after = job_catalog_service.get_listing_match(db_session, profile, listing.id)
    assert after.readiness > before.readiness
    assert len(after.matched_skills) >= 3
    assert len(after.missing_skills) < len(before.missing_skills)


def test_recommended_listings_ranks_by_actual_match_quality(db_session):
    profile = _make_profile(db_session, "recommended@example.com")
    for skill_name in ["Java", "SQL", "System Design"]:
        _give_resume_evidence(db_session, profile, skill_name, weight=0.95)

    results = job_catalog_service.recommended_listings(db_session, profile, limit=10)
    assert len(results) == 10
    readiness_values = [r.readiness or 0 for r in results]
    assert readiness_values == sorted(readiness_values, reverse=True)


def test_tracking_is_capped_at_five_and_never_duplicates(db_session):
    profile = _make_profile(db_session, "tracked@example.com")
    listings = db_session.scalars(select(CompanyJobListing).limit(6)).all()
    assert len(listings) == 6

    for listing in listings[:5]:
        job_catalog_service.track_job(db_session, profile, listing.id)

    with pytest.raises(ConflictError):
        job_catalog_service.track_job(db_session, profile, listings[5].id)

    # Tracking an already-tracked job again is a no-op, not a duplicate or an error.
    again = job_catalog_service.track_job(db_session, profile, listings[0].id)
    tracked = job_catalog_service.get_tracked_jobs(db_session, profile)
    assert len(tracked) == 5
    assert again.listing_id == listings[0].id

    job_catalog_service.untrack_job(db_session, profile, listings[0].id)
    assert len(job_catalog_service.get_tracked_jobs(db_session, profile)) == 4
    # Freed a slot -- the 6th listing can now be tracked.
    job_catalog_service.track_job(db_session, profile, listings[5].id)
    assert len(job_catalog_service.get_tracked_jobs(db_session, profile)) == 5


def test_untrack_unknown_job_raises_not_found(db_session):
    profile = _make_profile(db_session, "untrack-404@example.com")
    listing = db_session.scalar(select(CompanyJobListing))
    with pytest.raises(NotFoundError):
        job_catalog_service.untrack_job(db_session, profile, listing.id)


def test_tracked_jobs_are_isolated_per_student(db_session):
    profile_a = _make_profile(db_session, "isolation-a@example.com")
    profile_b = _make_profile(db_session, "isolation-b@example.com")
    listing = db_session.scalar(select(CompanyJobListing))

    job_catalog_service.track_job(db_session, profile_a, listing.id)
    assert len(job_catalog_service.get_tracked_jobs(db_session, profile_a)) == 1
    assert len(job_catalog_service.get_tracked_jobs(db_session, profile_b)) == 0


def test_gap_simulator_estimates_hours_only_for_real_gaps(db_session):
    profile = _make_profile(db_session, "gap-plan@example.com")
    listing = db_session.scalar(select(CompanyJobListing).where(CompanyJobListing.company == "Zerodha"))
    assert listing is not None

    required_reqs = [r for r in listing.requirements if r.is_required]
    plan = job_catalog_service.simulate_job_gap(db_session, profile, listing.id, weekly_commitment_hours=10)
    assert plan.missing_count == len(required_reqs)
    assert plan.total_estimated_hours > 0
    assert plan.estimated_weeks_to_ready == -(-plan.total_estimated_hours // 10)  # ceil division
    assert any("heuristic" in a.lower() for a in plan.assumptions)
    assert all(item.estimated_hours > 0 for item in plan.items)

    for req in required_reqs:
        _give_resume_evidence(db_session, profile, req.skill.name, weight=0.95)

    fully_ready_plan = job_catalog_service.simulate_job_gap(db_session, profile, listing.id)
    assert fully_ready_plan.missing_count == 0
    assert fully_ready_plan.partial_count == 0
    assert fully_ready_plan.total_estimated_hours == 0
    assert fully_ready_plan.estimated_weeks_to_ready == 0
    assert fully_ready_plan.items == []
