"""Live job feed: normalisation of a mocked Greenhouse board, endless cursor
wrap, skill extraction with importance tags, and the curated-catalog fallback
when every board is unreachable.
"""

import httpx

from app.services import live_jobs_service

_GH_JOBS = {
    "jobs": [
        {
            "id": 101,
            "title": "Software Engineer, Backend",
            "updated_at": "2026-08-30T10:00:00Z",
            "location": {"name": "Remote - US"},
            "absolute_url": "https://boards.greenhouse.io/example/jobs/101",
            "departments": [{"name": "Infrastructure"}],
            "content": (
                "&lt;p&gt;Own core services end to end.&lt;/p&gt;"
                "&lt;h3&gt;What you&#39;ll do&lt;/h3&gt;&lt;ul&gt;"
                "&lt;li&gt;Design and build distributed systems in Python and Go&lt;/li&gt;"
                "&lt;li&gt;Own reliability, on-call, and design docs&lt;/li&gt;&lt;/ul&gt;"
                "&lt;h3&gt;Requirements&lt;/h3&gt;&lt;ul&gt;"
                "&lt;li&gt;Strong data structures and algorithms&lt;/li&gt;"
                "&lt;li&gt;Experience with PostgreSQL, Redis, Docker and Kubernetes&lt;/li&gt;"
                "&lt;li&gt;You have shipped production Python services&lt;/li&gt;&lt;/ul&gt;"
                "&lt;h3&gt;Nice to have&lt;/h3&gt;&lt;ul&gt;&lt;li&gt;GraphQL&lt;/li&gt;&lt;/ul&gt;"
            ),
        },
        {
            "id": 102,
            "title": "Frontend Engineer",
            "updated_at": "2026-08-29T10:00:00Z",
            "location": {"name": "New York, NY"},
            "absolute_url": "https://boards.greenhouse.io/example/jobs/102",
            "departments": [{"name": "Product"}],
            "content": (
                "&lt;p&gt;Build the product UI.&lt;/p&gt;&lt;h3&gt;Requirements&lt;/h3&gt;&lt;ul&gt;"
                "&lt;li&gt;Expert React, TypeScript and JavaScript&lt;/li&gt;"
                "&lt;li&gt;Strong CSS and testing&lt;/li&gt;&lt;/ul&gt;"
            ),
        },
        {
            "id": 104,
            "title": "Software Engineering Intern, Summer 2026",
            "updated_at": "2026-08-28T10:00:00Z",
            "location": {"name": "Bengaluru, India"},
            "absolute_url": "https://boards.greenhouse.io/example/jobs/104",
            "departments": [{"name": "Eng"}],
            "content": "&lt;p&gt;A 12-week internship.&lt;/p&gt;&lt;h3&gt;Requirements&lt;/h3&gt;&lt;ul&gt;&lt;li&gt;Data structures, Python&lt;/li&gt;&lt;/ul&gt;",
        },
        {"id": 103, "title": "Office Manager", "content": "&lt;p&gt;Not an eng role&lt;/p&gt;", "location": {"name": "SF"}},
    ]
}


class _Resp:
    def __init__(self, payload, status=200):
        self._p = payload
        self.status_code = status

    def json(self):
        return self._p

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError("boom")


class _FakeClient:
    def __init__(self, *a, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def get(self, url, params=None):
        if "greenhouse" in url:
            return _Resp(_GH_JOBS)
        return _Resp([])  # lever boards return nothing in this test


class _BrokenClient(_FakeClient):
    def get(self, url, params=None):
        raise httpx.ConnectError("no network")


class _FakeRedis:
    def __init__(self):
        self._d = {}

    def get(self, k):
        return self._d.get(k)

    def set(self, k, v, ex=None):
        self._d[k] = v


def _register(client, email):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "Live Jobs Student"},
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_feed_normalises_live_board_jobs(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-feed@example.com")

    body = client.get("/api/v1/job-catalog/live?cursor=0&limit=8&kind=all", headers=headers).json()
    assert body["live"] is True
    assert body["total"] > 0
    live_jobs = [j for j in body["jobs"] if j["is_live"]]
    assert live_jobs, "expected at least one job pulled from a live board"
    job = live_jobs[0]
    assert job["id"].startswith("greenhouse:")
    assert job["url"].startswith("http")
    for s in job["skills"]:
        assert s["importance"] in ("core", "strong", "familiar")


def test_feed_splits_jobs_from_internships(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-intern@example.com")

    interns = client.get("/api/v1/job-catalog/live?limit=20&kind=internships", headers=headers).json()
    assert interns["total"] > 0
    assert all(j["is_internship"] is True for j in interns["jobs"])
    assert any("intern" in j["title"].lower() for j in interns["jobs"])

    jobs = client.get("/api/v1/job-catalog/live?limit=20&kind=jobs", headers=headers).json()
    assert all(j["is_internship"] is False for j in jobs["jobs"])


def test_feed_includes_indian_openings(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-india@example.com")

    body = client.get(
        "/api/v1/job-catalog/live/search?location=India&kind=all", headers=headers
    ).json()
    assert body["total"] > 0
    assert all("india" in j["location"].lower() for j in body["jobs"])


def test_feed_cursor_wraps_forever(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-wrap@example.com")

    cursor = 0
    seen_pages = 0
    for _ in range(6):
        body = client.get(f"/api/v1/job-catalog/live?cursor={cursor}&limit=3", headers=headers).json()
        assert len(body["jobs"]) == 3  # never runs dry
        cursor = body["next_cursor"]
        seen_pages += 1
    assert seen_pages == 6


def test_feed_falls_back_to_catalog(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _BrokenClient)
    headers = _register(client, "live-fallback@example.com")

    body = client.get("/api/v1/job-catalog/live?limit=5", headers=headers).json()
    assert body["live"] is False
    assert body["total"] > 0
    assert all(j["is_live"] is False for j in body["jobs"])
    assert any(j["company"] == "Google" for j in client.get("/api/v1/job-catalog/live?limit=20", headers=headers).json()["jobs"])


def test_live_detail_lookup(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-detail@example.com")

    feed = client.get("/api/v1/job-catalog/live?limit=3", headers=headers).json()
    job_id = feed["jobs"][0]["id"]
    detail = client.get(f"/api/v1/job-catalog/live-detail?id={job_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["id"] == job_id

    missing = client.get("/api/v1/job-catalog/live-detail?id=greenhouse:nope:999", headers=headers)
    assert missing.status_code == 404


def test_skill_match_for_arbitrary_names(client) -> None:
    headers = _register(client, "live-skillmatch@example.com")
    body = client.get(
        "/api/v1/job-catalog/skill-match",
        headers=headers,
        params={"skills": "Python, System Design, Totally Made Up Skill"},
    ).json()
    # No resume evidence for a fresh student -> everything known is missing,
    # the unknown name is also missing, readiness is a real fraction.
    assert body["readiness"] == 0.0
    assert "Totally Made Up Skill" in body["missing"]
    assert set(body["matched"]) == set()
    assert "Python" in body["missing"] and "System Design" in body["missing"]

    empty = client.get("/api/v1/job-catalog/skill-match", headers=headers, params={"skills": ""}).json()
    assert empty["readiness"] is None


def test_live_search_filters_to_real_jobs(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-search@example.com")

    body = client.get("/api/v1/job-catalog/live/search?q=Backend", headers=headers).json()
    assert body["live"] is True
    assert body["total"] > 0
    assert all("backend" in j["title"].lower() for j in body["jobs"])
    assert any(j["is_live"] is True for j in body["jobs"])

    by_company = client.get("/api/v1/job-catalog/live/search?q=Figma", headers=headers).json()
    assert by_company["total"] >= 1
    assert all(j["company"] == "Figma" for j in by_company["jobs"])

    by_skill = client.get("/api/v1/job-catalog/live/search?skills=Kubernetes,Docker", headers=headers).json()
    assert all(
        {"kubernetes", "docker"}.issubset({s["name"].lower() for s in j["skills"]}) for j in by_skill["jobs"]
    )


def test_track_a_live_job_creates_a_tracked_listing(client, monkeypatch) -> None:
    monkeypatch.setattr(live_jobs_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(live_jobs_service.httpx, "Client", _FakeClient)
    headers = _register(client, "live-track@example.com")

    feed = client.get("/api/v1/job-catalog/live?limit=4", headers=headers).json()
    job = feed["jobs"][0]

    tracked = client.post("/api/v1/job-catalog/live/track", headers=headers, json={"id": job["id"]})
    assert tracked.status_code == 201
    body = tracked.json()
    assert body["match"]["listing"]["company"] == job["company"]
    # readiness is computed from real skill requirements
    assert body["match"]["readiness"] is not None

    tracked_list = client.get("/api/v1/job-catalog/tracked", headers=headers).json()
    assert any(t["match"]["listing"]["company"] == job["company"] for t in tracked_list)

    # tracking the same live job again is idempotent (no duplicate listing)
    again = client.post("/api/v1/job-catalog/live/track", headers=headers, json={"id": job["id"]})
    assert again.status_code == 201
    assert len(client.get("/api/v1/job-catalog/tracked", headers=headers).json()) == 1
