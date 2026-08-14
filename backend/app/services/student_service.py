from sqlalchemy.orm import Session

from app.models.audit import AuditEvent
from app.models.student import StudentProfile
from app.schemas.student import StudentProfileUpdateRequest


def update_profile_details(
    db: Session, student_profile: StudentProfile, payload: StudentProfileUpdateRequest
) -> StudentProfile:
    changed_fields: list[str] = []
    updates = payload.model_dump(exclude_unset=True)

    for field_name, value in updates.items():
        if getattr(student_profile, field_name) != value:
            setattr(student_profile, field_name, value)
            changed_fields.append(field_name)

    if changed_fields:
        db.add(
            AuditEvent(
                student_profile_id=student_profile.id,
                event_type="profile_details_updated",
                payload={"changed_fields": changed_fields},
            )
        )
        db.commit()
        db.refresh(student_profile)

    return student_profile


def set_camera_consent(db: Session, student_profile: StudentProfile, enabled: bool) -> None:
    student_profile.consent_settings = {**student_profile.consent_settings, "camera_consent": enabled}
    db.commit()
