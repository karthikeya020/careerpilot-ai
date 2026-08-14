"""Tests for the GitHub coding-profile widget: not_configured empty state,
the real-data ok path (mocked GitHub responses -- no live network call in
tests), not_found, unavailable-with-no-cache, and a cache hit skipping the
second HTTP call. Mirrors the monkeypatch-based mocking style already used
in test_graphrag.py rather than adding a new test dependency.
"""

import httpx

from app.services import github_profile_service


def _register_and_auth(client, email="github-profile@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "GitHub Profile Student"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"status {self.status_code}")


class _FakeHttpxClient:
    call_count = 0

    def __init__(self, responses):
        self._responses = responses

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, path, params=None):
        _FakeHttpxClient.call_count += 1
        return self._responses[path]


class _BrokenHttpxClient:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, path, params=None):
        raise httpx.ConnectError("no network")


class _FakeRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ex=None):
        self._store[key] = value


def _ok_responses(username="octostudent"):
    return {
        f"/users/{username}": _FakeResponse(
            200,
            {
                "name": "Octo Student",
                "bio": "Building things",
                "avatar_url": "https://example.com/avatar.png",
                "html_url": f"https://github.com/{username}",
                "public_repos": 12,
                "followers": 34,
                "created_at": "2020-01-01T00:00:00Z",
            },
        ),
        f"/users/{username}/repos": _FakeResponse(
            200,
            [
                {
                    "name": "repo-a",
                    "html_url": "https://github.com/x/repo-a",
                    "language": "Python",
                    "stargazers_count": 10,
                    "pushed_at": "2026-01-01T00:00:00Z",
                    "fork": False,
                },
                {
                    "name": "repo-b",
                    "html_url": "https://github.com/x/repo-b",
                    "language": "TypeScript",
                    "stargazers_count": 2,
                    "pushed_at": "2026-01-02T00:00:00Z",
                    "fork": False,
                },
                {
                    "name": "forked-repo",
                    "html_url": "https://github.com/x/forked-repo",
                    "language": "Python",
                    "stargazers_count": 100,
                    "pushed_at": "2026-01-03T00:00:00Z",
                    "fork": True,
                },
            ],
        ),
        f"/users/{username}/events/public": _FakeResponse(200, []),
    }


def test_not_configured_when_no_github_username_set(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/students/me/github-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "not_configured"


def test_ok_path_with_mocked_github_responses(client, monkeypatch) -> None:
    headers = _register_and_auth(client, email="github-ok@example.com")
    client.patch("/api/v1/students/me", headers=headers, json={"github_username": "octostudent"})

    monkeypatch.setattr(github_profile_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(github_profile_service.httpx, "Client", lambda **kw: _FakeHttpxClient(_ok_responses()))

    response = client.get("/api/v1/students/me/github-profile", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["public_repos"] == 12
    # The forked repo is excluded -- only the two owned repos count.
    assert body["language_breakdown"] == {"Python": 1, "TypeScript": 1}
    assert len(body["top_repos"]) == 2


def test_not_found_returns_typed_status_not_http_error(client, monkeypatch) -> None:
    headers = _register_and_auth(client, email="github-404@example.com")
    client.patch("/api/v1/students/me", headers=headers, json={"github_username": "doesnotexistuser404"})

    monkeypatch.setattr(github_profile_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(
        github_profile_service.httpx,
        "Client",
        lambda **kw: _FakeHttpxClient({"/users/doesnotexistuser404": _FakeResponse(404, {})}),
    )

    response = client.get("/api/v1/students/me/github-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_unavailable_when_network_fails_and_no_cache(client, monkeypatch) -> None:
    headers = _register_and_auth(client, email="github-down@example.com")
    client.patch("/api/v1/students/me", headers=headers, json={"github_username": "octostudent"})

    monkeypatch.setattr(github_profile_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(github_profile_service.httpx, "Client", lambda **kw: _BrokenHttpxClient())

    response = client.get("/api/v1/students/me/github-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_fresh_cache_hit_skips_second_http_call(monkeypatch) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(github_profile_service, "get_redis", lambda: fake_redis)
    _FakeHttpxClient.call_count = 0
    monkeypatch.setattr(github_profile_service.httpx, "Client", lambda **kw: _FakeHttpxClient(_ok_responses()))

    first = github_profile_service.fetch_profile("octostudent")
    assert first.status == "ok"
    assert _FakeHttpxClient.call_count == 3  # user, repos, events

    second = github_profile_service.fetch_profile("octostudent")
    assert second.status == "ok"
    assert _FakeHttpxClient.call_count == 3  # unchanged -- served from cache, no new HTTP calls


def test_last_good_cache_survives_a_later_outage(monkeypatch) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(github_profile_service, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(github_profile_service.httpx, "Client", lambda **kw: _FakeHttpxClient(_ok_responses()))

    first = github_profile_service.fetch_profile("octostudent")
    assert first.status == "ok"

    # Force the fresh cache to miss (as it would after its TTL expires) so
    # the next call is forced back onto the network, which is now down.
    fake_redis._store.pop(github_profile_service._fresh_key("octostudent"))
    monkeypatch.setattr(github_profile_service.httpx, "Client", lambda **kw: _BrokenHttpxClient())

    second = github_profile_service.fetch_profile("octostudent")
    assert second.status == "ok"
    assert second.public_repos == 12
