import uuid

from app.models.retrieval import SOURCE_TYPE_RESUME
from app.services import retrieval_service


def test_index_and_search_returns_relevant_chunk(db_session):
    source_id = uuid.uuid4()
    retrieval_service.index_document(
        db_session,
        source_type=SOURCE_TYPE_RESUME,
        source_id=source_id,
        text="Built a FastAPI backend with PostgreSQL and SQL joins for reporting.\n\nUsed React for the frontend.",
    )

    result = retrieval_service.search(db_session, query_text="SQL joins PostgreSQL backend")
    assert not result.missing_context_warning
    assert len(result.items) >= 1
    assert "SQL" in result.items[0].text or "PostgreSQL" in result.items[0].text
    assert result.confidence > 0


def test_search_with_no_documents_returns_missing_context_warning(db_session):
    result = retrieval_service.search(db_session, query_text="anything at all")
    assert result.missing_context_warning is True
    assert result.items == []
    assert result.confidence == 0.0


def test_indexing_same_text_twice_is_idempotent(db_session):
    source_id = uuid.uuid4()
    first = retrieval_service.index_document(db_session, SOURCE_TYPE_RESUME, source_id, "Some resume text here.")
    second = retrieval_service.index_document(db_session, SOURCE_TYPE_RESUME, source_id, "Some resume text here.")
    assert len(first) == 1
    assert len(second) == 0


def test_search_scoped_to_student_profile(db_session):
    student_a = uuid.uuid4()
    student_b = uuid.uuid4()
    retrieval_service.index_document(
        db_session, SOURCE_TYPE_RESUME, uuid.uuid4(), "Kubernetes and Docker containerization expert.",
        student_profile_id=student_a,
    )
    retrieval_service.index_document(
        db_session, SOURCE_TYPE_RESUME, uuid.uuid4(), "Kubernetes and Docker containerization expert.",
        student_profile_id=student_b,
    )

    result = retrieval_service.search(db_session, query_text="Kubernetes Docker", student_profile_id=student_a)
    assert len(result.items) == 1
