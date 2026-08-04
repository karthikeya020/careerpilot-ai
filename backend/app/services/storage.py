"""Local-disk file storage adapter.

Swappable behind this module boundary: a future S3/GCS-backed implementation
only needs to satisfy `save(student_id, filename, content) -> storage_path`
and `read(storage_path) -> bytes`.
"""

import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()


DOCUMENT_SUFFIXES = (".pdf", ".docx", ".txt")
AUDIO_SUFFIXES = (".webm", ".ogg", ".wav", ".mp3", ".m4a", ".mp4")


def _safe_suffix(original_filename: str, allowed: tuple[str, ...] = DOCUMENT_SUFFIXES) -> str:
    suffix = Path(original_filename).suffix.lower()
    return suffix if suffix in allowed else ""


def save(student_profile_id: uuid.UUID, original_filename: str, content: bytes) -> str:
    student_dir = settings.upload_dir / str(student_profile_id)
    student_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{_safe_suffix(original_filename)}"
    destination = student_dir / safe_name
    destination.write_bytes(content)
    return str(destination.relative_to(settings.upload_dir))


def save_audio(student_profile_id: uuid.UUID, original_filename: str, content: bytes) -> str:
    student_dir = settings.upload_dir / str(student_profile_id) / "interview_audio"
    student_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}{_safe_suffix(original_filename, AUDIO_SUFFIXES)}"
    destination = student_dir / safe_name
    destination.write_bytes(content)
    return str(destination.relative_to(settings.upload_dir))


def read(storage_path: str) -> bytes:
    return (settings.upload_dir / storage_path).read_bytes()
