"""Security regression tests: rate limiting (real, against live Redis) and
audio-upload validation (size limit + type allowlist), both fixed during
the Phase 3 security review after being found absent/unenforced.
"""

import io
import uuid

import pytest

from app.core.rate_limit import RateLimitedError, RateLimiter


class _FakeClient:
    def __init__(self, host: str) -> None:
        self.host = host


class _FakeRequest:
    def __init__(self, host: str) -> None:
        self.client = _FakeClient(host)


def test_rate_limiter_blocks_after_threshold():
    limiter = RateLimiter(key_prefix=f"test-{uuid.uuid4()}", max_requests=3, window_seconds=5)
    request = _FakeRequest("1.2.3.4")
    for _ in range(3):
        limiter(request)  # under the limit -- must not raise
    with pytest.raises(RateLimitedError):
        limiter(request)


def test_rate_limiter_is_isolated_per_client_ip():
    limiter = RateLimiter(key_prefix=f"test-{uuid.uuid4()}", max_requests=1, window_seconds=5)
    limiter(_FakeRequest("1.1.1.1"))
    limiter(_FakeRequest("2.2.2.2"))  # different IP -- independent budget
    with pytest.raises(RateLimitedError):
        limiter(_FakeRequest("1.1.1.1"))


def _register_and_auth(client, email="security-regression@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Security Regression Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_oversized_audio_upload_is_rejected(client) -> None:
    headers = _register_and_auth(client, email="oversized-audio@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    # 16MB, one byte over the 15MB default limit.
    oversized_audio = io.BytesIO(b"0" * (16 * 1024 * 1024))
    response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={"question_id": question["id"], "typed_answer_text": "fallback answer text"},
        files={"audio": ("answer.webm", oversized_audio, "audio/webm")},
    )
    assert response.status_code == 422
    assert "exceeds" in response.json()["error"]["message"].lower()


def test_disallowed_audio_extension_is_rejected(client) -> None:
    headers = _register_and_auth(client, email="bad-audio-extension@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    malicious = io.BytesIO(b"#!/bin/sh\necho hi\n")
    response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={"question_id": question["id"], "typed_answer_text": "fallback answer text"},
        files={"audio": ("payload.sh", malicious, "audio/webm")},
    )
    assert response.status_code == 422
    assert "unsupported audio file type" in response.json()["error"]["message"].lower()


def test_disallowed_audio_mime_type_is_rejected(client) -> None:
    headers = _register_and_auth(client, email="bad-audio-mime@example.com")
    start = client.post("/api/v1/interviews/sessions", headers=headers, json={"mode": "hr"})
    body = start.json()
    session_id = body["session"]["id"]
    question = body["next_question"]

    payload = io.BytesIO(b"<html><script>alert(1)</script></html>")
    response = client.post(
        f"/api/v1/interviews/sessions/{session_id}/answers",
        headers=headers,
        data={"question_id": question["id"], "typed_answer_text": "fallback answer text"},
        files={"audio": ("answer.webm", payload, "text/html")},
    )
    assert response.status_code == 422
    assert "unsupported audio content type" in response.json()["error"]["message"].lower()


def test_unexpected_error_response_never_leaks_internals(client) -> None:
    # A malformed UUID path param triggers FastAPI's validation error path,
    # not the generic exception handler -- but it's the one built-in way to
    # confirm the error envelope never echoes raw exception internals to
    # the client regardless of which handler answers.
    headers = _register_and_auth(client, email="error-envelope@example.com")
    response = client.get("/api/v1/interviews/sessions/not-a-valid-uuid", headers=headers)
    assert response.status_code in (404, 422)
    body = response.json()
    assert "error" in body
    assert "traceback" not in str(body).lower()
    assert "site-packages" not in str(body)
