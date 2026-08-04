"""Deterministic reranker: weighted sum of vector similarity, keyword
overlap, recency, and role relevance. No LLM call -- reranking a shortlist
of already-retrieved candidates is exactly the kind of task Constitution
rule/Prompt-2 guidance ("simple deterministic calculation: do not invoke an
LLM") says should stay deterministic.
"""

import re

from app.ai.schemas import RerankCandidate, RerankedItem

_WEIGHTS = {
    "vector": 0.55,
    "keyword_overlap": 0.2,
    "recency": 0.15,
    "role_relevance": 0.1,
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _keyword_overlap(query: str, text: str) -> float:
    query_tokens = set(_TOKEN_RE.findall(query.lower()))
    text_tokens = set(_TOKEN_RE.findall(text.lower()))
    if not query_tokens:
        return 0.0
    return len(query_tokens & text_tokens) / len(query_tokens)


class SimpleReranker:
    name = "simple-weighted-v1"

    def rerank(self, query: str, candidates: list[RerankCandidate]) -> list[RerankedItem]:
        results = []
        for candidate in candidates:
            keyword_score = _keyword_overlap(query, candidate.text)
            recency_score = float(candidate.metadata.get("recency_score", 0.5))
            role_score = float(candidate.metadata.get("role_relevance_score", 0.5))
            combined = (
                _WEIGHTS["vector"] * candidate.base_score
                + _WEIGHTS["keyword_overlap"] * keyword_score
                + _WEIGHTS["recency"] * recency_score
                + _WEIGHTS["role_relevance"] * role_score
            )
            results.append(
                RerankedItem(
                    id=candidate.id,
                    score=round(combined, 4),
                    components={
                        "vector": round(candidate.base_score, 4),
                        "keyword_overlap": round(keyword_score, 4),
                        "recency": round(recency_score, 4),
                        "role_relevance": round(role_score, 4),
                    },
                )
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return results
