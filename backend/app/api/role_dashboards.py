import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile, require_role
from app.core.errors import ForbiddenError, NotFoundError
from app.core.redis_client import get_redis
from app.graphrag.neo4j_client import is_graph_available
from app.models.student import StudentProfile
from app.schemas.resume import RecruiterCardOut
from app.schemas.role_dashboard import (
    AdminDashboardOut,
    FacultyDashboardOut,
    PlacementDashboardOut,
    RecruiterCandidateOut,
    SetRecruiterVisibilityRequest,
)
from app.services import role_dashboard_service
from app.services.recruiter_card_service import build_recruiter_card
from app.services.resume_service import get_latest_resume

router = APIRouter(tags=["role-dashboards"])


@router.get("/faculty/dashboard", response_model=FacultyDashboardOut)
def faculty_dashboard(
    db: Session = Depends(get_db), _user=Depends(require_role("faculty", "administrator"))
) -> dict:
    return role_dashboard_service.get_faculty_dashboard(db)


@router.get("/placement/dashboard", response_model=PlacementDashboardOut)
def placement_dashboard(
    db: Session = Depends(get_db), _user=Depends(require_role("placement_staff", "administrator"))
) -> dict:
    return role_dashboard_service.get_placement_dashboard(db)


@router.get("/recruiter/candidates", response_model=list[RecruiterCandidateOut])
def recruiter_candidates(
    db: Session = Depends(get_db), _user=Depends(require_role("recruiter", "administrator"))
) -> list[dict]:
    return role_dashboard_service.get_recruiter_candidates(db)


@router.get("/admin/dashboard", response_model=AdminDashboardOut)
def admin_dashboard(db: Session = Depends(get_db), _user=Depends(require_role("administrator"))) -> dict:
    try:
        redis_ok = bool(get_redis().ping())
    except Exception:
        redis_ok = False
    return role_dashboard_service.get_admin_dashboard(db, graph_available=is_graph_available(), redis_ok=redis_ok)


@router.get("/recruiter/candidates/{student_profile_id}/evidence-card", response_model=RecruiterCardOut)
def recruiter_candidate_evidence_card(
    student_profile_id: uuid.UUID,
    db: Session = Depends(get_db),
    _user=Depends(require_role("recruiter", "administrator")),
) -> RecruiterCardOut:
    """The same evidence-completeness card the student sees about
    themselves -- gated on that student's own explicit recruiter_visible
    consent, never shown for a student who hasn't opted in (Constitution
    rule 5/6: no hiring verdict, no un-consented visibility)."""
    student_profile = db.get(StudentProfile, student_profile_id)
    if student_profile is None:
        raise NotFoundError("Student not found.")
    if student_profile.consent_settings.get("recruiter_visible") is not True:
        raise ForbiddenError("This student has not opted in to recruiter visibility.")
    resume = get_latest_resume(db, student_profile.id)
    card = build_recruiter_card(db, student_profile, resume)
    return RecruiterCardOut(**card.__dict__)


@router.put("/students/me/recruiter-visibility", status_code=204)
def set_my_recruiter_visibility(
    payload: SetRecruiterVisibilityRequest,
    student_profile=Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> None:
    role_dashboard_service.set_recruiter_visibility(db, student_profile, payload.visible)
