import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile
from app.core.errors import NotFoundError
from app.models.job_catalog import CompanyJobListing, TrackedJob
from app.models.student import StudentProfile
from app.schemas.job_catalog import (
    CompanyJobListingOut,
    GapPlanItemOut,
    JobGapPlanOut,
    JobListingMatchOut,
    SectorOut,
    TrackedJobOut,
)
from app.schemas.job_roadmap import JobRoadmapOut
from app.schemas.live_jobs import (
    LiveJobFeedOut,
    LiveJobOut,
    LiveJobSearchOut,
    SkillMatchOut,
    TrackLiveJobRequest,
)
from app.services import job_catalog_service, job_roadmap_service, live_jobs_service
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


@router.get("/live", response_model=LiveJobFeedOut)
def live_feed(
    cursor: int = Query(default=0, ge=0),
    limit: int = Query(default=8, ge=1, le=20),
    kind: str = Query(default="jobs", pattern="^(jobs|internships|all)$"),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LiveJobFeedOut:
    return LiveJobFeedOut(**live_jobs_service.get_feed(db, cursor=cursor, limit=limit, kind=kind))


@router.get("/live-detail", response_model=LiveJobOut)
def live_job_detail(
    id: str = Query(..., min_length=3, max_length=200),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LiveJobOut:
    job = live_jobs_service.get_job(db, id)
    if job is None:
        raise NotFoundError("That job isn't in the current feed anymore.")
    return job


@router.get("/live/search", response_model=LiveJobSearchOut)
def live_search(
    q: str = Query(default="", max_length=120),
    sector: str = Query(default="", max_length=30),
    location: str = Query(default="", max_length=80),
    remote: bool = Query(default=False),
    skills: str = Query(default="", max_length=400),
    min_package: float = Query(default=0.0, ge=0, le=200),
    kind: str = Query(default="all", pattern="^(jobs|internships|all)$"),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> LiveJobSearchOut:
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    return LiveJobSearchOut(
        **live_jobs_service.search_feed(
            db,
            q=q,
            sector=sector,
            location=location,
            remote=remote,
            skills=skill_list,
            min_package=min_package,
            kind=kind,
        )
    )


@router.post("/live/track", response_model=TrackedJobOut, status_code=201)
def track_live(
    payload: TrackLiveJobRequest,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> TrackedJobOut:
    tracked = job_catalog_service.track_live_job(db, student_profile, payload.id)
    tracked_ids = _tracked_listing_ids(db, student_profile)
    match = job_catalog_service.get_listing_match(db, student_profile, tracked.listing_id)
    return TrackedJobOut(id=tracked.id, created_at=tracked.created_at, match=_match_out(match, tracked_ids))


@router.get("/skill-match", response_model=SkillMatchOut)
def skill_match(
    skills: str = Query(default="", max_length=800),
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> SkillMatchOut:
    names = [s.strip() for s in skills.split(",") if s.strip()]
    return SkillMatchOut(**job_catalog_service.match_skill_names(db, student_profile, names))


@router.get("/roadmap", response_model=JobRoadmapOut)
def roadmap_for_query(
    company: str = Query(..., min_length=1, max_length=150),
    title: str = Query(..., min_length=1, max_length=200),
    sector: str = Query(default="startup", max_length=30),
    seniority: str | None = Query(default=None, max_length=50),
    skills: str = Query(default="", max_length=600),
    student_profile: StudentProfile = Depends(get_current_student_profile),
) -> JobRoadmapOut:
    skill_list = [s.strip() for s in skills.split(",") if s.strip()]
    return job_roadmap_service.build_roadmap(company, title, sector, seniority, skill_list)


@router.get("/{listing_id}/roadmap", response_model=JobRoadmapOut)
def roadmap_for_listing(
    listing_id: uuid.UUID,
    student_profile: StudentProfile = Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> JobRoadmapOut:
    listing = db.get(CompanyJobListing, listing_id)
    if listing is None:
        raise NotFoundError("Job listing not found.")
    skills = [r.skill.name for r in listing.requirements if r.is_required]
    return job_roadmap_service.build_roadmap(
        listing.company, listing.title, listing.sector, listing.seniority, skills
    )


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
