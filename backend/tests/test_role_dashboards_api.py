"""Faculty, placement-cell, recruiter, and administrator dashboards:
real cohort aggregates, role-restricted access, and recruiter visibility
requiring explicit student opt-in (never a full-cohort leak).
"""

from sqlalchemy import select

from app.models.user import Role, User, UserRole


def _register_student(client, email="student-for-dashboards@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Dashboard Test Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _make_role_user(db_session, role_name: str, email: str) -> dict:
    from app.core.security import create_access_token, hash_password

    role = db_session.scalar(select(Role).where(Role.name == role_name))
    user = User(email=email, password_hash=hash_password("Password1"))
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(user.id, [role_name])
    return {"Authorization": f"Bearer {token}"}


def test_faculty_dashboard_requires_faculty_role(client, db_session) -> None:
    student_headers = _register_student(client)
    forbidden = client.get("/api/v1/faculty/dashboard", headers=student_headers)
    assert forbidden.status_code == 403

    faculty_headers = _make_role_user(db_session, "faculty", "faculty-dashboards@example.com")
    allowed = client.get("/api/v1/faculty/dashboard", headers=faculty_headers)
    assert allowed.status_code == 200
    body = allowed.json()
    assert "cohort_skill_gaps" in body
    assert len(body["cohort_skill_gaps"]) == 6
    assert "students_needing_support" in body
    # Constitution rule 6: no public ranking -- confirm no per-student score list is exposed here.
    assert "ranking" not in str(body).lower()


def test_placement_dashboard_shows_aggregate_distribution_not_individuals(client, db_session) -> None:
    placement_headers = _make_role_user(db_session, "placement_staff", "placement-dashboards@example.com")
    response = client.get("/api/v1/placement/dashboard", headers=placement_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["readiness_distribution"]) == 5
    assert "not a hiring or placement guarantee" in body["disclaimer"].lower()
    assert "full_name" not in str(body)


def test_recruiter_only_sees_consented_students(client, db_session) -> None:
    student_headers = _register_student(client, email="opt-in-student@example.com")
    recruiter_headers = _make_role_user(db_session, "recruiter", "recruiter-dashboards@example.com")

    before = client.get("/api/v1/recruiter/candidates", headers=recruiter_headers)
    assert before.status_code == 200
    assert before.json() == []

    opt_in = client.put(
        "/api/v1/students/me/recruiter-visibility", headers=student_headers, json={"visible": True}
    )
    assert opt_in.status_code == 204

    after = client.get("/api/v1/recruiter/candidates", headers=recruiter_headers)
    assert after.status_code == 200
    names = [c["full_name"] for c in after.json()]
    assert "Dashboard Test Student" in names
    for candidate in after.json():
        assert candidate["consent_status"] == "explicit_opt_in"
        # No automatic hiring recommendation field of any kind.
        assert "hire" not in str(candidate).lower()
        assert "probability" not in str(candidate).lower()


def test_recruiter_dashboard_requires_recruiter_role(client) -> None:
    student_headers = _register_student(client, email="not-a-recruiter@example.com")
    response = client.get("/api/v1/recruiter/candidates", headers=student_headers)
    assert response.status_code == 403


def test_admin_dashboard_requires_admin_role_and_shows_real_health(client, db_session) -> None:
    faculty_headers = _make_role_user(db_session, "faculty", "faculty-not-admin@example.com")
    forbidden = client.get("/api/v1/admin/dashboard", headers=faculty_headers)
    assert forbidden.status_code == 403

    admin_headers = _make_role_user(db_session, "administrator", "admin-dashboards@example.com")
    response = client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["service_health"]["database"] is True
    assert "care_execution_stats" in body
    assert sum(body["users_by_role"].values()) == body["total_users"]
    assert body["total_users"] >= 2  # at least the faculty + admin users just created


def test_recruiter_visibility_toggle_requires_student_auth(client, db_session) -> None:
    admin_headers = _make_role_user(db_session, "administrator", "admin-not-student@example.com")
    response = client.put(
        "/api/v1/students/me/recruiter-visibility", headers=admin_headers, json={"visible": True}
    )
    assert response.status_code in (401, 403)
