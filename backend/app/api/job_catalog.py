import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.models.job_catalog import TrackedJob
from app.models.student import StudentProfile
from app.schemas.job_catalog import (
    CompanyJobListingOut,
    GapPlanItemOut,
    JobGapPlanOut,
    JobListingMatchOut,
    SectorOut,
    TrackedJobOut,
)
from app.services import job_catalog_service
from app.services.job_catalog_service import ListingMatch

router = APIRouter(prefix="/job-catalog", tags=["job-catalog"])


def _match_out(match: ListingMatch, tracked_listing_ids: set[uuid.UUID]) -> JobListingMatchOut:
    return JobListingMatchOut(
        listing=CompanyJobListingOut.model_validate(match.listing),
        matched_skills=match.matched_skills,
        partial_skills=match.partial_skills,
        missing_skills=match.missing_skills,
        readiness=match.readiness,
        is_tracked=match.listing.id in tracked_listing_ids,
    )


def _tracked_listing_ids(db: Session, student_profile: StudentProfile) -> set[uuid.UUID]:
    return {t.listing_id for t in job_catalog_service.get_tracked_jobs(db, student_profile)}


@router.get("/sectors", response_model=list[SectorOut])
def list_sectors(db: Session = Depends(get_db)) -> list[SectorOut]:
    return [SectorOut(**s) for s in job_catalog_service.list_sectors(db)]


@router.get("/recommended", response_model=list[JobListingMatchOut])
def recommended(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[JobListingMatchOut]:
    tracked_ids = _tracked_listing_ids(db, student_profile)
    matches = job_catalog_service.recommended_listings(db, student_profile)
    return [_match_out(m, tracked_ids) for m in matches]


@router.get("/search", response_model=list[JobListingMatchOut])
def search(
    sector: str | None = Query(default=None),
    company: str | None = Query(default=None),
    package_tier: str | None = Query(default=None),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[JobListingMatchOut]:
    tracked_ids = _tracked_listing_ids(db, student_profile)
    matches = job_catalog_service.search_listings(db, student_profile, sector=sector, company_query=company, package_tier=package_tier)
    return [_match_out(m, tracked_ids) for m in matches]


@router.get("/tracked", response_model=list[TrackedJobOut])
def list_tracked(
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> list[TrackedJobOut]:
    tracked_ids = _tracked_listing_ids(db, student_profile)
    result = []
    for tracked in job_catalog_service.get_tracked_jobs(db, student_profile):
        match = job_catalog_service.get_listing_match(db, student_profile, tracked.listing_id)
        result.append(TrackedJobOut(id=tracked.id, created_at=tracked.created_at, match=_match_out(match, tracked_ids)))
    return result


@router.post("/tracked/{listing_id}", response_model=TrackedJobOut, status_code=201)
def track(
    listing_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TrackedJobOut:
    tracked: TrackedJob = job_catalog_service.track_job(db, student_profile, listing_id)
    tracked_ids = _tracked_listing_ids(db, student_profile)
    match = job_catalog_service.get_listing_match(db, student_profile, listing_id)
    return TrackedJobOut(id=tracked.id, created_at=tracked.created_at, match=_match_out(match, tracked_ids))


@router.delete("/tracked/{listing_id}", status_code=204)
def untrack(
    listing_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> None:
    job_catalog_service.untrack_job(db, student_profile, listing_id)


@router.get("/{listing_id}", response_model=JobListingMatchOut)
def get_listing(
    listing_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> JobListingMatchOut:
    tracked_ids = _tracked_listing_ids(db, student_profile)
    match = job_catalog_service.get_listing_match(db, student_profile, listing_id)
    return _match_out(match, tracked_ids)


@router.get("/{listing_id}/gap-plan", response_model=JobGapPlanOut)
def gap_plan(
    listing_id: uuid.UUID,
    weekly_hours: float = Query(default=job_catalog_service.DEFAULT_WEEKLY_COMMITMENT_HOURS, ge=1, le=80),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> JobGapPlanOut:
    plan = job_catalog_service.simulate_job_gap(db, student_profile, listing_id, weekly_commitment_hours=weekly_hours)
    return JobGapPlanOut(
        listing=CompanyJobListingOut.model_validate(plan.listing),
        readiness=plan.readiness,
        matched_count=plan.matched_count,
        partial_count=plan.partial_count,
        missing_count=plan.missing_count,
        total_estimated_hours=plan.total_estimated_hours,
        weekly_commitment_hours=plan.weekly_commitment_hours,
        estimated_weeks_to_ready=plan.estimated_weeks_to_ready,
        items=[GapPlanItemOut(**vars(item)) for item in plan.items],
        assumptions=plan.assumptions,
    )
