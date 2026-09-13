"""Tests for the LeetCode progress tracker: not_configured empty state, the
real-data ok path (mocked GraphQL response -- no live network call in
tests), not_found when the handle doesn't resolve, unavailable-with-no-cache,
a fresh-cache hit skipping the second HTTP call, and last-known-good
surviving a later outage. Mirrors the monkeypatch-based mocking style of
test_github_profile.py.
"""

import json
from datetime import datetime, timedelta, timezone

import httpx

from app.services import leetcode_profile_service


def _register_and_auth(client, email="leetcode-profile@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password1", "full_name": "LeetCode Profile Student"},
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

    def __init__(self, body):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None):
        _FakeHttpxClient.call_count += 1
        return _FakeResponse(200, self._body)


class _BrokenHttpxClient:
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None):
        raise httpx.ConnectError("no network")


class _FakeRedis:
    def __init__(self):
        self._store: dict[str, str] = {}

    def get(self, key):
        return self._store.get(key)

    def set(self, key, value, ex=None):
        self._store[key] = value


def _calendar_for_last_n_days(n: int) -> str:
    today = datetime.now(timezone.utc).date()
    entries: dict[str, int] = {}
    for offset in range(n):
        day = today - timedelta(days=offset)
        ts = int(datetime(day.year, day.month, day.day, tzinfo=timezone.utc).timestamp())
        entries[str(ts)] = 2
    return json.dumps(entries)


def _ok_body(username="octostudent", streak_days=5):
    return {
        "data": {
            "matchedUser": {
                "username": username,
                "profile": {
                    "realName": "Octo Student",
                    "userAvatar": "https://example.com/avatar.png",
                    "ranking": 123456,
                },
                "submitStatsGlobal": {
                    "acSubmissionNum": [
                        {"difficulty": "All", "count": 210, "submissions": 400},
                        {"difficulty": "Easy", "count": 100, "submissions": 150},
                        {"difficulty": "Medium", "count": 90, "submissions": 200},
                        {"difficulty": "Hard", "count": 20, "submissions": 50},
                    ],
                    "totalSubmissionNum": [
                        {"difficulty": "All", "count": 210, "submissions": 500},
                        {"difficulty": "Easy", "count": 100, "submissions": 180},
                        {"difficulty": "Medium", "count": 90, "submissions": 250},
                        {"difficulty": "Hard", "count": 20, "submissions": 70},
                    ],
                },
                "languageProblemCount": [
                    {"languageName": "C++", "problemsSolved": 60},
                    {"languageName": "Python3", "problemsSolved": 150},
                ],
                "badges": [{"id": "1"}, {"id": "2"}],
                "userCalendar": {
                    "streak": streak_days,
                    "totalActiveDays": 120,
                    "submissionCalendar": _calendar_for_last_n_days(streak_days),
                },
                "previousYearCalendar": {"submissionCalendar": "{}"},
            },
            "allQuestionsCount": [
                {"difficulty": "All", "count": 3500},
                {"difficulty": "Easy", "count": 900},
                {"difficulty": "Medium", "count": 1800},
                {"difficulty": "Hard", "count": 800},
            ],
            "userContestRanking": {
                "attendedContestsCount": 8,
                "rating": 1650.7,
                "globalRanking": 45000,
                "topPercentage": 22.5,
            },
            "userContestRankingHistory": [
                {
                    "attended": False,
                    "ranking": 0,
                    "problemsSolved": 0,
                    "totalProblems": 4,
                    "contest": {"title": "Weekly Contest 100", "startTime": 1600000000},
                },
                {
                    "attended": True,
                    "ranking": 5000,
                    "problemsSolved": 3,
                    "totalProblems": 4,
                    "contest": {"title": "Weekly Contest 390", "startTime": 1710000000},
                },
            ],
        }
    }


def test_not_configured_when_no_leetcode_username_set(client) -> None:
    headers = _register_and_auth(client)
    response = client.get("/api/v1/students/me/leetcode-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "not_configured"


def test_ok_path_with_mocked_leetcode_response(client, monkeypatch) -> None:
    headers = _register_and_auth(client, email="leetcode-ok@example.com")
    client.patch("/api/v1/students/me", headers=headers, json={"leetcode_username": "octostudent"})

    monkeypatch.setattr(leetcode_profile_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(leetcode_profile_service.httpx, "Client", lambda **kw: _FakeHttpxClient(_ok_body()))

    response = client.get("/api/v1/students/me/leetcode-profile", headers=headers)
    assert response.status_code == 200
    body = response.json()

    assert body["status"] == "ok"
    assert body["total_solved"] == 210
    assert body["easy_solved"] == 100 and body["easy_total"] == 900
    assert body["medium_solved"] == 90 and body["medium_total"] == 1800
    assert body["hard_solved"] == 20 and body["hard_total"] == 800
    assert body["total_questions"] == 3500
    # 400 accepted submissions / 500 total submissions.
    assert body["acceptance_rate"] == 80.0
    # Calendar seeded with 5 consecutive active days ending today.
    assert body["current_streak_days"] == 5
    assert body["longest_streak_days"] == 5
    assert body["active_days_last_year"] == 5
    assert len(body["activity_heatmap"]) == 5
    assert body["total_active_days"] == 120
    # Languages sorted by problems solved, descending.
    assert [row["language"] for row in body["language_stats"]] == ["Python3", "C++"]
    assert body["badges_count"] == 2
    assert body["contests_attended"] == 8
    assert body["contest_rating"] == 1651  # rounded to a whole number
    assert body["contest_top_percentage"] == 22.5
    # Only the attended contest is surfaced in history.
    assert len(body["recent_contests"]) == 1
    assert body["recent_contests"][0]["title"] == "Weekly Contest 390"
    assert body["profile_url"] == "https://leetcode.com/octostudent/"


def test_not_found_when_matched_user_is_null(client, monkeypatch) -> None:
    headers = _register_and_auth(client, email="leetcode-404@example.com")
    client.patch("/api/v1/students/me", headers=headers, json={"leetcode_username": "doesnotexist404"})

    monkeypatch.setattr(leetcode_profile_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(
        leetcode_profile_service.httpx,
        "Client",
        lambda **kw: _FakeHttpxClient({"data": {"matchedUser": None}}),
    )

    response = client.get("/api/v1/students/me/leetcode-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "not_found"


def test_unavailable_when_network_fails_and_no_cache(client, monkeypatch) -> None:
    headers = _register_and_auth(client, email="leetcode-down@example.com")
    client.patch("/api/v1/students/me", headers=headers, json={"leetcode_username": "octostudent"})

    monkeypatch.setattr(leetcode_profile_service, "get_redis", lambda: _FakeRedis())
    monkeypatch.setattr(leetcode_profile_service.httpx, "Client", lambda **kw: _BrokenHttpxClient())

    response = client.get("/api/v1/students/me/leetcode-profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"


def test_fresh_cache_hit_skips_second_http_call(monkeypatch) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(leetcode_profile_service, "get_redis", lambda: fake_redis)
    _FakeHttpxClient.call_count = 0
    monkeypatch.setattr(leetcode_profile_service.httpx, "Client", lambda **kw: _FakeHttpxClient(_ok_body()))

    first = leetcode_profile_service.fetch_profile("octostudent")
    assert first.status == "ok"
    assert _FakeHttpxClient.call_count == 1

    second = leetcode_profile_service.fetch_profile("octostudent")
    assert second.status == "ok"
    assert _FakeHttpxClient.call_count == 1  # served from cache, no new HTTP call


def test_last_good_cache_survives_a_later_outage(monkeypatch) -> None:
    fake_redis = _FakeRedis()
    monkeypatch.setattr(leetcode_profile_service, "get_redis", lambda: fake_redis)
    monkeypatch.setattr(leetcode_profile_service.httpx, "Client", lambda **kw: _FakeHttpxClient(_ok_body()))

    first = leetcode_profile_service.fetch_profile("octostudent")
    assert first.status == "ok"

    fake_redis._store.pop(leetcode_profile_service._fresh_key("octostudent"))
    monkeypatch.setattr(leetcode_profile_service.httpx, "Client", lambda **kw: _BrokenHttpxClient())

    second = leetcode_profile_service.fetch_profile("octostudent")
    assert second.status == "ok"
    assert second.total_solved == 210
