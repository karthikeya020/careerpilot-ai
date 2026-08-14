"""Job Match catalog service: dream-company search across a curated listing
catalog (see app/seed/company_job_catalog.py for why it's curated, not
scraped), resume-evidence-based readiness scoring (the exact same weighting
as job_description_service's JD matching -- one scoring system, not two), a
capped "I want this job" tracked list, and a deterministic Job Gap
Simulator. No number here is invented: readiness comes from real
SkillEvidence, and the gap-plan hour estimates are explicitly labeled as a
heuristic planning assumption (Constitution rule 4).
"""

import math
import uuid
from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.models.job_catalog import ALL_SECTORS, SECTOR_LABELS, CompanyJobListing, TrackedJob
from app.models.skill import Skill
from app.models.student import StudentProfile
from app.services import resource_service
from app.services.job_description_service import resume_weight_by_skill

MAX_TRACKED_JOBS = 5
SEARCH_RESULT_TARGET = 10
_FULL_MATCH_WEIGHT_THRESHOLD = 0.85

# Heuristic hours-to-close-the-gap per skill, by current evidence status -- a
# documented planning assumption, not a measured learning rate.
_HOURS_MISSING_SKILL = 14
_HOURS_PARTIAL_SKILL = 6
DEFAULT_WEEKLY_COMMITMENT_HOURS = 10

_PACKAGE_TIER_MIN_LPA = {"10": 10, "20": 20, "30": 30, "40": 40}


@dataclass
class ListingMatch:
    listing: CompanyJobListing
    matched_skills: list[Skill] = field(default_factory=list)
    partial_skills: list[Skill] = field(default_factory=list)
    missing_skills: list[Skill] = field(default_factory=list)
    readiness: float | None = None


def _score_listing(listing: CompanyJobListing, weight_by_skill: dict[uuid.UUID, float]) -> ListingMatch:
    match = ListingMatch(listing=listing)
    seen: set[uuid.UUID] = set()
    for req in listing.requirements:
        if not req.is_required or req.skill_id in seen:
            continue
        seen.add(req.skill_id)
        weight = weight_by_skill.get(req.skill_id)
        if weight is None:
            match.missing_skills.append(req.skill)
        elif weight >= _FULL_MATCH_WEIGHT_THRESHOLD:
            match.matched_skills.append(req.skill)
        else:
            match.partial_skills.append(req.skill)

    total = len(match.matched_skills) + len(match.partial_skills) + len(match.missing_skills)
    match.readiness = round((len(match.matched_skills) + 0.5 * len(match.partial_skills)) / total, 4) if total else None
    return match


def _all_listings(db: Session) -> list[CompanyJobListing]:
    return list(db.scalars(select(CompanyJobListing)).all())


def list_sectors(db: Session) -> list[dict]:
    counts: dict[str, int] = {}
    for listing in _all_listings(db):
        counts[listing.sector] = counts.get(listing.sector, 0) + 1
    return [{"slug": s, "label": SECTOR_LABELS[s], "listing_count": counts.get(s, 0)} for s in ALL_SECTORS]


def _package_ok(listing: CompanyJobListing, package_tier: str | None) -> bool:
    if not package_tier or package_tier == "any":
        return True
    tier_min = _PACKAGE_TIER_MIN_LPA.get(package_tier, 0)
    return float(listing.package_max_lpa) >= tier_min


def search_listings(
    db: Session,
    student_profile: StudentProfile,
    sector: str | None = None,
    company_query: str | None = None,
    package_tier: str | None = None,
    limit: int = SEARCH_RESULT_TARGET,
) -> list[ListingMatch]:
    """Always tries to return `limit` results: listings matching every filter
    come first (best readiness first), padded with the closest same-sector
    listings so a specific company search never dead-ends on one card --
    exactly the "9 similar companies too" behavior requested."""
    weight_by_skill = resume_weight_by_skill(db, student_profile.id)
    listings = _all_listings(db)
    query_lower = (company_query or "").strip().lower()

    def matches_query(listing: CompanyJobListing) -> bool:
        if not query_lower:
            return True
        return query_lower in listing.company.lower() or query_lower in listing.title.lower()

    primary = [
        listing
        for listing in listings
        if (not sector or listing.sector == sector) and _package_ok(listing, package_tier) and matches_query(listing)
    ]
    primary_ids = {listing.id for listing in primary}

    combined = list(primary)
    if len(combined) < limit:
        pad_sector = sector or (primary[0].sector if primary else None)
        pad_pool = [
            listing
            for listing in listings
            if listing.id not in primary_ids and _package_ok(listing, package_tier) and (pad_sector is None or listing.sector == pad_sector)
        ]
        combined.extend(pad_pool)
    if len(combined) < limit:
        seen_ids = {listing.id for listing in combined}
        pad_pool = [listing for listing in listings if listing.id not in seen_ids and _package_ok(listing, package_tier)]
        combined.extend(pad_pool)

    scored = [_score_listing(listing, weight_by_skill) for listing in combined]
    primary_scored = sorted((m for m in scored if m.listing.id in primary_ids), key=lambda m: -(m.readiness or 0))
    pad_scored = sorted((m for m in scored if m.listing.id not in primary_ids), key=lambda m: -(m.readiness or 0))
    return (primary_scored + pad_scored)[:limit]


def recommended_listings(db: Session, student_profile: StudentProfile, limit: int = SEARCH_RESULT_TARGET) -> list[ListingMatch]:
    """No search input required -- ranks the whole catalog by how well the
    student's actual resume evidence already covers each role, so "auto-fill
    based on my resume" is the very first thing a student sees."""
    weight_by_skill = resume_weight_by_skill(db, student_profile.id)
    scored = [_score_listing(listing, weight_by_skill) for listing in _all_listings(db)]
    scored.sort(key=lambda m: -(m.readiness or 0))
    return scored[:limit]


def get_listing_match(db: Session, student_profile: StudentProfile, listing_id: uuid.UUID) -> ListingMatch:
    listing = db.get(CompanyJobListing, listing_id)
    if listing is None:
        raise NotFoundError("Job listing not found.")
    weight_by_skill = resume_weight_by_skill(db, student_profile.id)
    return _score_listing(listing, weight_by_skill)


def get_tracked_jobs(db: Session, student_profile: StudentProfile) -> list[TrackedJob]:
    return list(
        db.scalars(
            select(TrackedJob).where(TrackedJob.student_profile_id == student_profile.id).order_by(TrackedJob.created_at)
        ).all()
    )


def track_job(db: Session, student_profile: StudentProfile, listing_id: uuid.UUID) -> TrackedJob:
    listing = db.get(CompanyJobListing, listing_id)
    if listing is None:
        raise NotFoundError("Job listing not found.")

    existing = db.scalar(
        select(TrackedJob).where(TrackedJob.student_profile_id == student_profile.id, TrackedJob.listing_id == listing_id)
    )
    if existing is not None:
        return existing

    current_count = (
        db.scalar(select(func.count()).select_from(TrackedJob).where(TrackedJob.student_profile_id == student_profile.id))
        or 0
    )
    if current_count >= MAX_TRACKED_JOBS:
        raise ConflictError(
            f"You can track up to {MAX_TRACKED_JOBS} dream jobs at a time. Remove one before adding another."
        )

    tracked = TrackedJob(student_profile_id=student_profile.id, listing_id=listing_id)
    db.add(tracked)
    db.commit()
    db.refresh(tracked)
    return tracked


def untrack_job(db: Session, student_profile: StudentProfile, listing_id: uuid.UUID) -> None:
    tracked = db.scalar(
        select(TrackedJob).where(TrackedJob.student_profile_id == student_profile.id, TrackedJob.listing_id == listing_id)
    )
    if tracked is None:
        raise NotFoundError("This job isn't in your tracked list.")
    db.delete(tracked)
    db.commit()


# ---- Job Gap Simulator: what to work on, how much, how, and how far away ----


@dataclass
class GapPlanItem:
    skill_name: str
    status: str  # "missing" | "partial"
    estimated_hours: float
    recommended_resource: dict | None


@dataclass
class JobGapPlan:
    listing: CompanyJobListing
    readiness: float | None
    matched_count: int
    partial_count: int
    missing_count: int
    total_estimated_hours: float
    weekly_commitment_hours: float
    estimated_weeks_to_ready: int
    items: list[GapPlanItem]
    assumptions: list[str]


def _best_resource_for_skill(db: Session, skill: Skill) -> dict | None:
    resources = resource_service.list_resources(db, skill_name=skill.name)
    if not resources:
        return None
    best = max(resources, key=lambda r: float(r.quality_score))
    return {"id": str(best.id), "title": best.title, "url": best.url, "duration_minutes": best.duration_minutes}


def simulate_job_gap(
    db: Session,
    student_profile: StudentProfile,
    listing_id: uuid.UUID,
    weekly_commitment_hours: float = DEFAULT_WEEKLY_COMMITMENT_HOURS,
) -> JobGapPlan:
    listing = db.get(CompanyJobListing, listing_id)
    if listing is None:
        raise NotFoundError("Job listing not found.")

    weight_by_skill = resume_weight_by_skill(db, student_profile.id)
    match = _score_listing(listing, weight_by_skill)

    items: list[GapPlanItem] = []
    total_hours = 0.0
    for skill in match.missing_skills:
        items.append(
            GapPlanItem(
                skill_name=skill.name, status="missing", estimated_hours=_HOURS_MISSING_SKILL,
                recommended_resource=_best_resource_for_skill(db, skill),
            )
        )
        total_hours += _HOURS_MISSING_SKILL
    for skill in match.partial_skills:
        items.append(
            GapPlanItem(
                skill_name=skill.name, status="partial", estimated_hours=_HOURS_PARTIAL_SKILL,
                recommended_resource=_best_resource_for_skill(db, skill),
            )
        )
        total_hours += _HOURS_PARTIAL_SKILL

    items.sort(key=lambda i: (i.status != "missing", -i.estimated_hours))
    weekly_commitment_hours = max(1.0, weekly_commitment_hours)
    weeks = math.ceil(total_hours / weekly_commitment_hours) if total_hours > 0 else 0

    assumptions = [
        f"Assumes {weekly_commitment_hours:.0f} focused hours/week -- adjust this to fit your real schedule.",
        f"Missing skills are estimated at {_HOURS_MISSING_SKILL}h to build real evidence from scratch; "
        f"partially-supported skills at {_HOURS_PARTIAL_SKILL}h to strengthen further. This is a heuristic "
        "planning estimate, not a measured learning rate or a guarantee.",
    ]
    if not items:
        assumptions.append("Every required skill for this role already has strong resume evidence on file.")

    return JobGapPlan(
        listing=listing,
        readiness=match.readiness,
        matched_count=len(match.matched_skills),
        partial_count=len(match.partial_skills),
        missing_count=len(match.missing_skills),
        total_estimated_hours=total_hours,
        weekly_commitment_hours=weekly_commitment_hours,
        estimated_weeks_to_ready=weeks,
        items=items,
        assumptions=assumptions,
    )
