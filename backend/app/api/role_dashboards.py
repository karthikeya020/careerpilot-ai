from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import get_current_student_profile, require_role
from app.core.redis_client import get_redis
from app.graphrag.neo4j_client import is_graph_available
from app.schemas.role_dashboard import (
    AdminDashboardOut,
    FacultyDashboardOut,
    PlacementDashboardOut,
    RecruiterCandidateOut,
    SetRecruiterVisibilityRequest,
)
from app.services import role_dashboard_service

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


@router.put("/students/me/recruiter-visibility", status_code=204)
def set_my_recruiter_visibility(
    payload: SetRecruiterVisibilityRequest,
    student_profile=Depends(get_current_student_profile),
    db: Session = Depends(get_db),
) -> None:
    role_dashboard_service.set_recruiter_visibility(db, student_profile, payload.visible)
