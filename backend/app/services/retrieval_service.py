"""Hybrid retrieval: chunk text, embed it (HashingEmbeddingProvider by
default -- see PHASE_2_EXECUTION_PLAN §2.2 for why embeddings are stored as
JSON rather than a native pgvector column), and search by cosine similarity
combined with structured filters, then rerank with SimpleReranker. Returns a
structured result with scores, source citations, and an explicit
missing-context warning -- never silently returns nothing without saying so.
"""

import hashlib
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.embeddings.hashing import cosine_similarity
from app.ai.registry import get_embedding_provider, get_reranker
from app.ai.schemas import RerankCandidate
from app.models.retrieval import RetrievalDocument

_CHUNK_MAX_CHARS = 800
_MISSING_CONTEXT_SCORE_THRESHOLD = 0.15


def _chunk_text(text: str, max_chars: int = _CHUNK_MAX_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = paragraph
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def index_document(
    db: Session,
    source_type: str,
    source_id: uuid.UUID,
    text: str,
    student_profile_id: uuid.UUID | None = None,
    target_role_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> list[RetrievalDocument]:
    provider = get_embedding_provider()
    chunks = _chunk_text(text)
    created: list[RetrievalDocument] = []

    for index, chunk in enumerate(chunks):
        text_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
        existing = db.scalar(
            select(RetrievalDocument).where(
                RetrievalDocument.source_type == source_type,
                RetrievalDocument.source_id == source_id,
                RetrievalDocument.text_hash == text_hash,
            )
        )
        if existing:
            continue

        embedding_result = provider.embed([chunk])[0]
        document = RetrievalDocument(
            source_type=source_type,
            source_id=source_id,
            student_profile_id=student_profile_id,
            target_role_id=target_role_id,
            chunk_index=index,
            text=chunk,
            text_hash=text_hash,
            embedding=embedding_result.vector,
            embedding_model=embedding_result.model,
            metadata_json=metadata or {},
        )
        db.add(document)
        created.append(document)

    if created:
        db.commit()
        for doc in created:
            db.refresh(doc)
    return created


@dataclass
class RetrievedItem:
    document_id: str
    source_type: str
    source_id: str
    text: str
    score: float
    components: dict[str, float]


@dataclass
class HybridRetrievalResult:
    items: list[RetrievedItem]
    confidence: float
    missing_context_warning: bool


def search(
    db: Session,
    query_text: str,
    student_profile_id: uuid.UUID | None = None,
    source_types: list[str] | None = None,
    top_k: int = 5,
) -> HybridRetrievalResult:
    embedding_provider = get_embedding_provider()
    reranker = get_reranker()

    query_stmt = select(RetrievalDocument)
    if student_profile_id is not None:
        query_stmt = query_stmt.where(RetrievalDocument.student_profile_id == student_profile_id)
    if source_types:
        query_stmt = query_stmt.where(RetrievalDocument.source_type.in_(source_types))
    candidates = db.scalars(query_stmt).all()

    if not candidates:
        return HybridRetrievalResult(items=[], confidence=0.0, missing_context_warning=True)

    query_vector = embedding_provider.embed([query_text])[0].vector
    rerank_candidates = []
    similarity_by_id = {}
    for doc in candidates:
        similarity = cosine_similarity(query_vector, doc.embedding)
        similarity_by_id[str(doc.id)] = similarity
        rerank_candidates.append(
            RerankCandidate(
                id=str(doc.id),
                text=doc.text,
                base_score=similarity,
                metadata={"recency_score": 0.5, "role_relevance_score": 0.5},
            )
        )

    ranked = reranker.rerank(query_text, rerank_candidates)[:top_k]
    doc_by_id = {str(d.id): d for d in candidates}

    items = [
        RetrievedItem(
            document_id=r.id,
            source_type=doc_by_id[r.id].source_type,
            source_id=str(doc_by_id[r.id].source_id),
            text=doc_by_id[r.id].text,
            score=r.score,
            components=r.components,
        )
        for r in ranked
    ]

    top_score = items[0].score if items else 0.0
    missing_context_warning = not items or top_score < _MISSING_CONTEXT_SCORE_THRESHOLD
    confidence = round(min(top_score * 1.2, 0.95), 4) if items else 0.0

    return HybridRetrievalResult(items=items, confidence=confidence, missing_context_warning=missing_context_warning)


@dataclass
class HybridSearchResult(HybridRetrievalResult):
    graph_paths: list[list[str]]


def hybrid_search(
    db: Session,
    query_text: str,
    student_profile_id: uuid.UUID | None = None,
    source_types: list[str] | None = None,
    concept_slug: str | None = None,
    top_k: int = 5,
) -> HybridSearchResult:
    """Combines vector similarity search over indexed documents with graph
    relationship context for a concept -- the two retrieval strategies
    docs/04_KNOWLEDGE_GRAPH.md's "Hybrid Retrieval Strategy" section
    describes. If `concept_slug` is omitted, this degrades to vector-only
    search with an empty `graph_paths` list (still a real, honest result)."""
    vector_result = search(db, query_text, student_profile_id=student_profile_id, source_types=source_types, top_k=top_k)

    graph_paths: list[list[str]] = []
    if concept_slug:
        from app.graphrag.service import get_concept_neighborhood

        snapshot = get_concept_neighborhood(db, concept_slug)
        label_by_id = {n.id: n.label for n in snapshot.nodes}
        for edge in snapshot.edges:
            graph_paths.append([label_by_id.get(edge.source, edge.source), edge.relationship, label_by_id.get(edge.target, edge.target)])

    missing_context = vector_result.missing_context_warning and not graph_paths
    return HybridSearchResult(
        items=vector_result.items,
        confidence=vector_result.confidence,
        missing_context_warning=missing_context,
        graph_paths=graph_paths,
    )
