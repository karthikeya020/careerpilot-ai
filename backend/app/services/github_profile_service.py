"""GitHub coding-profile service -- real evidence for the Career Twin's
GitHub widget (Constitution rule 1/4: never fabricate a stat). Official
GitHub REST API only: LeetCode and HackerRank have no official public API,
so per product decision they're out of scope entirely rather than scraped.

No token required -- unauthenticated REST calls are enough for public
profile/repo/event data, at GitHub's standard 60 requests/hour/IP limit.
Results are Redis-cached (same fail-open posture as
app/core/rate_limit.py: a cold/unreachable Redis never blocks the feature,
it just means no caching) at two tiers:
  - a short "fresh" cache (1 hour) so repeated dashboard loads don't burn
    the rate limit or add latency;
  - a long "last known good" cache (30 days), only ever written from a
    successful `ok` fetch, returned when a live fetch fails so a demo
    doesn't go blank just because GitHub or the network is briefly down
    (Constitution rule 13: demo-critical features need a deterministic
    fallback). If neither cache has anything, the honest answer is
    `status="unavailable"` -- never an invented number.
"""

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.core.redis_client import get_redis
from app.schemas.github_profile import GithubActivityDayOut, GithubProfileOut, GithubRepoOut

logger = logging.getLogger("careerpilot")

_API_BASE = "https://api.github.com"
_FRESH_TTL_SECONDS = 60 * 60
_LAST_GOOD_TTL_SECONDS = 60 * 60 * 24 * 30
_ACTIVITY_WINDOW_DAYS = 90
_TOP_REPOS_LIMIT = 5
_REQUEST_TIMEOUT_SECONDS = 8.0


def _fresh_key(username: str) -> str:
    return f"github_profile:fresh:{username.lower()}"


def _last_good_key(username: str) -> str:
    return f"github_profile:last_good:{username.lower()}"


def _read_cache(key: str) -> GithubProfileOut | None:
    try:
        raw = get_redis().get(key)
    except Exception:
        return None
    if not raw:
        return None
    try:
        return GithubProfileOut.model_validate_json(raw)
    except Exception:
        return None


def _write_cache(key: str, profile: GithubProfileOut, ttl_seconds: int) -> None:
    try:
        get_redis().set(key, profile.model_dump_json(), ex=ttl_seconds)
    except Exception:
        logger.warning("GitHub profile cache write failed for key=%s -- continuing without caching", key)


def _fetch_from_github(username: str) -> GithubProfileOut:
    now = datetime.now(timezone.utc)
    with httpx.Client(
        base_url=_API_BASE,
        headers={"Accept": "application/vnd.github+json", "User-Agent": "CareerPilotAI"},
        timeout=_REQUEST_TIMEOUT_SECONDS,
    ) as client:
        user_response = client.get(f"/users/{username}")
        if user_response.status_code == 404:
            return GithubProfileOut(status="not_found", username=username)
        user_response.raise_for_status()
        user_data = user_response.json()

        repos_response = client.get(f"/users/{username}/repos", params={"per_page": 100, "sort": "pushed"})
        repos_response.raise_for_status()
        repos_data = repos_response.json()

        events_response = client.get(f"/users/{username}/events/public", params={"per_page": 100})
        events_response.raise_for_status()
        events_data = events_response.json()

    own_repos = [repo for repo in repos_data if not repo.get("fork")]

    language_counts: dict[str, int] = {}
    for repo in own_repos:
        language = repo.get("language")
        if language:
            language_counts[language] = language_counts.get(language, 0) + 1

    top_repos = [
        GithubRepoOut(
            name=repo["name"],
            html_url=repo["html_url"],
            language=repo.get("language"),
            stargazers_count=repo.get("stargazers_count", 0),
            pushed_at=repo.get("pushed_at"),
        )
        for repo in sorted(own_repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:_TOP_REPOS_LIMIT]
    ]

    cutoff = now - timedelta(days=_ACTIVITY_WINDOW_DAYS)
    activity_counts: dict[str, int] = {}
    for event in events_data:
        created_at = event.get("created_at")
        if not created_at:
            continue
        try:
            event_dt = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if event_dt < cutoff:
            continue
        day_key = event_dt.date().isoformat()
        activity_counts[day_key] = activity_counts.get(day_key, 0) + 1
    activity_heatmap = [GithubActivityDayOut(date=d, count=c) for d, c in sorted(activity_counts.items())]

    return GithubProfileOut(
        status="ok",
        username=username,
        name=user_data.get("name"),
        bio=user_data.get("bio"),
        avatar_url=user_data.get("avatar_url"),
        html_url=user_data.get("html_url") or f"https://github.com/{username}",
        public_repos=user_data.get("public_repos", 0),
        followers=user_data.get("followers", 0),
        account_created_at=user_data.get("created_at"),
        language_breakdown=language_counts,
        activity_heatmap=activity_heatmap,
        top_repos=top_repos,
        last_synced_at=now.isoformat(),
    )


def fetch_profile(username: str) -> GithubProfileOut:
    fresh = _read_cache(_fresh_key(username))
    if fresh is not None:
        return fresh

    try:
        profile = _fetch_from_github(username)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        last_good = _read_cache(_last_good_key(username))
        if last_good is not None:
            return last_good
        return GithubProfileOut(status="unavailable", username=username)

    _write_cache(_fresh_key(username), profile, _FRESH_TTL_SECONDS)
    if profile.status == "ok":
        _write_cache(_last_good_key(username), profile, _LAST_GOOD_TTL_SECONDS)
    return profile
