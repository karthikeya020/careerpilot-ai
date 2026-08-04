import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.core.types import GUID, JSONBType
from app.models.base import UUIDPKMixin, utcnow

SOURCE_TYPE_RESUME = "resume"
SOURCE_TYPE_JOB_DESCRIPTION = "job_description"
SOURCE_TYPE_RESOURCE = "resource"
SOURCE_TYPE_EVIDENCE_NOTE = "evidence_note"


class RetrievalDocument(UUIDPKMixin, Base):
    """A chunked, embedded unit of text used by hybrid retrieval.

    Embeddings are stored as JSON float arrays (see PHASE_2_EXECUTION_PLAN
    §2.2 for why this is used instead of a native pgvector column) and
    similarity is computed in Python at query time in
    `app/services/retrieval_service.py`.
    """

    __tablename__ = "retrieval_documents"

    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    source_id: Mapped[uuid.UUID] = mapped_column(GUID(), nullable=False, index=True)
    student_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("student_profiles.id", ondelete="CASCADE"), nullable=True, index=True
    )
    target_role_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True)
    chunk_index: Mapped[int] = mapped_column(nullable=False, default=0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    text_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    embedding: Mapped[list] = mapped_column(JSONBType(), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONBType(), default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utcnow, nullable=False)
