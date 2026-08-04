from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, UnauthorizedError
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.audit import AuditEvent
from app.models.student import StudentProfile
from app.models.user import RefreshToken, Role, User, UserRole


def get_role_by_name(db: Session, name: str) -> Role:
    role = db.scalar(select(Role).where(Role.name == name))
    if role is None:
        raise NotFoundError(f"Role '{name}' is not seeded. Run migrations before starting the API.")
    return role


def register_student(db: Session, email: str, password: str, full_name: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        raise ConflictError("An account with this email already exists")

    student_role = get_role_by_name(db, "student")

    user = User(email=email, password_hash=hash_password(password))
    db.add(user)
    db.flush()

    db.add(UserRole(user_id=user.id, role_id=student_role.id))
    db.add(StudentProfile(user_id=user.id, full_name=full_name, consent_settings={}))
    db.add(
        AuditEvent(
            user_id=user.id,
            event_type="user_registered",
            payload={"email": email},
        )
    )
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    if not user.is_active:
        raise UnauthorizedError("Account is disabled")

    db.add(
        AuditEvent(
            user_id=user.id,
            student_profile_id=user.student_profile.id if user.student_profile else None,
            event_type="user_login",
            payload={"email": email},
        )
    )
    db.commit()
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(user.id, user.role_names)


def issue_refresh_token(db: Session, user: User) -> str:
    raw, digest, expires_at = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=digest, expires_at=expires_at))
    db.commit()
    return raw


def rotate_refresh_token(db: Session, raw_token: str) -> tuple[User, str, str]:
    digest = hash_refresh_token(raw_token)
    token_row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == digest))
    if token_row is None or not token_row.is_active:
        raise UnauthorizedError("Invalid or expired refresh token")

    user = db.get(User, token_row.user_id)
    if user is None or not user.is_active:
        raise UnauthorizedError("Account is no longer active")

    from app.models.base import utcnow

    token_row.revoked_at = utcnow()
    db.add(token_row)

    new_access = issue_access_token(user)
    new_raw, new_digest, new_expires = generate_refresh_token()
    db.add(RefreshToken(user_id=user.id, token_hash=new_digest, expires_at=new_expires))
    db.commit()
    return user, new_access, new_raw


def revoke_refresh_token(db: Session, raw_token: str) -> None:
    digest = hash_refresh_token(raw_token)
    token_row = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == digest))
    if token_row is None:
        return
    from app.models.base import utcnow

    token_row.revoked_at = utcnow()
    db.add(token_row)
    db.commit()
