import pytest
from sqlalchemy import select

from app.core.deps import get_current_student_profile, require_role
from app.core.errors import ForbiddenError, UnauthorizedError
from app.models.student import StudentProfile
from app.models.user import Role, User, UserRole


def _make_user_with_role(db_session, role_name: str, email: str) -> User:
    role = db_session.scalar(select(Role).where(Role.name == role_name))
    user = User(email=email, password_hash="x")
    db_session.add(user)
    db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id))
    db_session.commit()
    db_session.refresh(user)
    return user


def test_require_role_allows_matching_role(db_session) -> None:
    user = _make_user_with_role(db_session, "student", "student-rbac@example.com")
    dependency = require_role("student")
    assert dependency(user=user) is user


def test_require_role_rejects_non_matching_role(db_session) -> None:
    user = _make_user_with_role(db_session, "faculty", "faculty-rbac@example.com")
    dependency = require_role("student")
    with pytest.raises(ForbiddenError):
        dependency(user=user)


def test_get_current_student_profile_errors_without_profile_row(db_session) -> None:
    user = _make_user_with_role(db_session, "student", "no-profile-rbac@example.com")
    with pytest.raises(UnauthorizedError):
        get_current_student_profile(user=user)


def test_get_current_student_profile_returns_profile(db_session) -> None:
    user = _make_user_with_role(db_session, "student", "with-profile-rbac@example.com")
    profile = StudentProfile(user_id=user.id, full_name="Has Profile")
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(user)

    result = get_current_student_profile(user=user)
    assert result.full_name == "Has Profile"
