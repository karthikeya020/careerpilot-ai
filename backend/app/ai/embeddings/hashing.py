"""Deterministic feature-hashing embedding.

This is a real, well-established embedding technique (the "hashing trick"),
not a random placeholder: each token is hashed into a fixed-size vector
index with a deterministic sign, and the accumulated vector is L2-normalized.
Documents that share vocabulary land closer together in cosine distance, so
similarity search behaves sensibly without requiring network access to an
embedding API -- which is what makes retrieval fully testable and demoable
offline. A real embedding-API adapter can be swapped in behind the same
`EmbeddingProvider` protocol without touching `retrieval_service.py`.
"""

import hashlib
import math
import re
import time

from app.ai.schemas import EmbeddingResult

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class HashingEmbeddingProvider:
    name = "hashing-v1"

    def __init__(self, dims: int = 128) -> None:
        self.dims = dims

    def _embed_one(self, text: str) -> list[float]:
        vector = [0.0] * self.dims
        for token in _tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.dims
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector))
        if norm > 0:
            vector = [v / norm for v in vector]
        return vector

    def embed(self, texts: list[str]) -> list[EmbeddingResult]:
        start = time.perf_counter()
        results = []
        for text in texts:
            vector = self._embed_one(text)
            results.append(
                EmbeddingResult(
                    vector=vector,
                    model=self.name,
                    dims=self.dims,
                    provider_name=self.name,
                    latency_ms=round((time.perf_counter() - start) * 1000, 3),
                )
            )
        return results


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
