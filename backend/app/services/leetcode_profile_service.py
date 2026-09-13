"""LeetCode coding-profile service -- real practice evidence for the
Assessment Arena's LeetCode progress tracker (Constitution rule 1/4:
never fabricate a stat).

LeetCode has no official public API, so this uses the same unauthenticated
GraphQL endpoint (`https://leetcode.com/graphql`) that powers the public
profile pages: because a LeetCode profile is public, the endpoint returns
solved counts, the submission calendar, and contest history for any
username without a token. Only public data is read; nothing is written.

Same fail-open, two-tier Redis caching posture as
app/services/github_profile_service.py:
  - a short "fresh" cache (1 hour) so repeated Assessment Arena loads
    don't hammer LeetCode or add latency;
  - a long "last known good" cache (30 days), only written from a
    successful `ok` fetch, returned when a live fetch fails so a demo
    doesn't go blank because LeetCode or the network is briefly down
    (Constitution rule 13). If neither cache has anything, the honest
    answer is `status="unavailable"` -- never an invented number.

Streaks and activity are computed here from LeetCode's own per-day
submission calendar, so they're derived from real counts rather than
estimated.
"""

import json
import logging
from datetime import date, datetime, timedelta, timezone

import httpx

from app.core.redis_client import get_redis
from app.schemas.leetcode_profile import (
    LeetCodeActivityDayOut,
    LeetCodeContestOut,
    LeetCodeLanguageStatOut,
    LeetCodeProfileOut,
)

logger = logging.getLogger("careerpilot")

_GRAPHQL_URL = "https://leetcode.com/graphql"
_FRESH_TTL_SECONDS = 60 * 60
_LAST_GOOD_TTL_SECONDS = 60 * 60 * 24 * 30
_ACTIVITY_WINDOW_DAYS = 90
_ACTIVE_DAYS_WINDOW_DAYS = 365
_TOP_LANGUAGES_LIMIT = 6
_RECENT_CONTESTS_LIMIT = 5
_REQUEST_TIMEOUT_SECONDS = 8.0

# One combined query -- profile, solved counts, submission calendar (this
# year + last year, so a streak can span the new-year boundary), languages,
# badges, and contest standing + history.
_PROFILE_QUERY = """
query careerPilotLeetCodeProfile($username: String!, $year: Int!, $prevYear: Int!) {
  matchedUser(username: $username) {
    username
    profile { realName userAvatar ranking }
    submitStatsGlobal {
      acSubmissionNum { difficulty count submissions }
      totalSubmissionNum { difficulty count submissions }
    }
    languageProblemCount { languageName problemsSolved }
    badges { id }
    userCalendar(year: $year) { streak totalActiveDays submissionCalendar }
    previousYearCalendar: userCalendar(year: $prevYear) { submissionCalendar }
  }
  allQuestionsCount { difficulty count }
  userContestRanking(username: $username) {
    attendedContestsCount
    rating
    globalRanking
    topPercentage
  }
  userContestRankingHistory(username: $username) {
    attended
    ranking
    problemsSolved
    totalProblems
    contest { title startTime }
  }
}
"""


def _fresh_key(username: str) -> str:
    return f"leetcode_profile:fresh:{username.lower()}"


def _last_good_key(username: str) -> str:
    return f"leetcode_profile:last_good:{username.lower()}"


def _read_cache(key: str) -> LeetCodeProfileOut | None:
    try:
        raw = get_redis().get(key)
    except Exception:
        return None
    if not raw:
        return None
    try:
        return LeetCodeProfileOut.model_validate_json(raw)
    except Exception:
        return None


def _write_cache(key: str, profile: LeetCodeProfileOut, ttl_seconds: int) -> None:
    try:
        get_redis().set(key, profile.model_dump_json(), ex=ttl_seconds)
    except Exception:
        logger.warning("LeetCode profile cache write failed for key=%s -- continuing without caching", key)


def _counts_by_difficulty(rows: list[dict] | None) -> dict[str, int]:
    """LeetCode returns difficulty buckets as {difficulty, count} rows with an
    'All' rollup row. Normalise to a lower-cased dict."""
    result: dict[str, int] = {}
    for row in rows or []:
        difficulty = str(row.get("difficulty", "")).lower()
        if difficulty:
            result[difficulty] = int(row.get("count", 0) or 0)
    return result


def _submissions_by_difficulty(rows: list[dict] | None) -> dict[str, int]:
    result: dict[str, int] = {}
    for row in rows or []:
        difficulty = str(row.get("difficulty", "")).lower()
        if difficulty:
            result[difficulty] = int(row.get("submissions", 0) or 0)
    return result


def _parse_submission_calendar(raw: str | None) -> dict[date, int]:
    """`submissionCalendar` is a JSON string mapping a UTC-midnight unix
    timestamp (seconds, as a string) to that day's submission count."""
    if not raw:
        return {}
    try:
        entries = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    by_day: dict[date, int] = {}
    for ts_str, count in entries.items():
        try:
            day = datetime.fromtimestamp(int(ts_str), tz=timezone.utc).date()
        except (ValueError, TypeError, OSError):
            continue
        by_day[day] = by_day.get(day, 0) + int(count or 0)
    return by_day


def _current_streak(active_days: set[date], today: date) -> int:
    """Consecutive active days ending today or yesterday -- not solving *yet*
    today shouldn't read as a broken streak."""
    anchor = today if today in active_days else today - timedelta(days=1)
    if anchor not in active_days:
        return 0
    streak = 0
    cursor = anchor
    while cursor in active_days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _longest_streak(active_days: set[date]) -> int:
    if not active_days:
        return 0
    longest = 0
    for day in active_days:
        if day - timedelta(days=1) in active_days:
            continue  # not the start of a run
        run = 0
        cursor = day
        while cursor in active_days:
            run += 1
            cursor += timedelta(days=1)
        longest = max(longest, run)
    return longest


def _build_contest_history(rows: list[dict] | None) -> list[LeetCodeContestOut]:
    attended = [row for row in (rows or []) if row.get("attended")]
    recent = attended[-_RECENT_CONTESTS_LIMIT:]
    recent.reverse()  # most recent first
    out: list[LeetCodeContestOut] = []
    for row in recent:
        contest = row.get("contest") or {}
        start_time = contest.get("startTime")
        start_iso = None
        if start_time:
            try:
                start_iso = datetime.fromtimestamp(int(start_time), tz=timezone.utc).isoformat()
            except (ValueError, TypeError, OSError):
                start_iso = None
        out.append(
            LeetCodeContestOut(
                title=contest.get("title") or "Contest",
                start_time=start_iso,
                ranking=row.get("ranking"),
                problems_solved=row.get("problemsSolved"),
                total_problems=row.get("totalProblems"),
            )
        )
    return out


def _fetch_from_leetcode(username: str) -> LeetCodeProfileOut:
    now = datetime.now(timezone.utc)
    today = now.date()
    variables = {"username": username, "year": today.year, "prevYear": today.year - 1}

    with httpx.Client(
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Referer": f"https://leetcode.com/{username}/",
            "Origin": "https://leetcode.com",
            "User-Agent": "CareerPilotAI (+https://leetcode.com/graphql public profile read)",
        },
        timeout=_REQUEST_TIMEOUT_SECONDS,
    ) as client:
        response = client.post(_GRAPHQL_URL, json={"query": _PROFILE_QUERY, "variables": variables})
        response.raise_for_status()
        body = response.json()

    data = (body or {}).get("data") or {}
    user = data.get("matchedUser")
    if not user:
        return LeetCodeProfileOut(status="not_found", username=username)

    profile = user.get("profile") or {}
    stats = user.get("submitStatsGlobal") or {}
    ac = _counts_by_difficulty(stats.get("acSubmissionNum"))
    ac_submissions = _submissions_by_difficulty(stats.get("acSubmissionNum"))
    total_submissions = _submissions_by_difficulty(stats.get("totalSubmissionNum"))
    bank = _counts_by_difficulty(data.get("allQuestionsCount"))

    acceptance_rate = None
    if total_submissions.get("all"):
        acceptance_rate = round(ac_submissions.get("all", 0) / total_submissions["all"] * 100, 1)

    calendar = _parse_submission_calendar((user.get("userCalendar") or {}).get("submissionCalendar"))
    calendar.update(_parse_submission_calendar((user.get("previousYearCalendar") or {}).get("submissionCalendar")))
    active_days = {day for day, count in calendar.items() if count > 0}

    heatmap_cutoff = today - timedelta(days=_ACTIVITY_WINDOW_DAYS)
    activity_heatmap = [
        LeetCodeActivityDayOut(date=day.isoformat(), count=count)
        for day, count in sorted(calendar.items())
        if day >= heatmap_cutoff and count > 0
    ]
    active_days_cutoff = today - timedelta(days=_ACTIVE_DAYS_WINDOW_DAYS)
    active_days_last_year = sum(1 for day in active_days if day >= active_days_cutoff)

    languages = sorted(
        (
            LeetCodeLanguageStatOut(
                language=row.get("languageName", "Unknown"),
                problems_solved=int(row.get("problemsSolved", 0) or 0),
            )
            for row in (user.get("languageProblemCount") or [])
        ),
        key=lambda item: item.problems_solved,
        reverse=True,
    )[:_TOP_LANGUAGES_LIMIT]

    contest_ranking = data.get("userContestRanking") or {}
    contest_rating = contest_ranking.get("rating")

    return LeetCodeProfileOut(
        status="ok",
        username=user.get("username") or username,
        real_name=profile.get("realName") or None,
        avatar_url=profile.get("userAvatar") or None,
        profile_url=f"https://leetcode.com/{user.get('username') or username}/",
        ranking=profile.get("ranking") or None,
        total_solved=ac.get("all", 0),
        total_questions=bank.get("all", 0),
        easy_solved=ac.get("easy", 0),
        easy_total=bank.get("easy", 0),
        medium_solved=ac.get("medium", 0),
        medium_total=bank.get("medium", 0),
        hard_solved=ac.get("hard", 0),
        hard_total=bank.get("hard", 0),
        acceptance_rate=acceptance_rate,
        current_streak_days=_current_streak(active_days, today),
        longest_streak_days=_longest_streak(active_days),
        active_days_last_year=active_days_last_year,
        total_active_days=int((user.get("userCalendar") or {}).get("totalActiveDays", 0) or 0),
        activity_heatmap=activity_heatmap,
        language_stats=languages,
        badges_count=len(user.get("badges") or []),
        contests_attended=int(contest_ranking.get("attendedContestsCount", 0) or 0),
        contest_rating=round(contest_rating) if contest_rating else None,
        contest_global_ranking=contest_ranking.get("globalRanking") or None,
        contest_top_percentage=contest_ranking.get("topPercentage") or None,
        recent_contests=_build_contest_history(data.get("userContestRankingHistory")),
        last_synced_at=now.isoformat(),
    )


def fetch_profile(username: str) -> LeetCodeProfileOut:
    fresh = _read_cache(_fresh_key(username))
    if fresh is not None:
        return fresh

    try:
        profile = _fetch_from_leetcode(username)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        last_good = _read_cache(_last_good_key(username))
        if last_good is not None:
            return last_good
        return LeetCodeProfileOut(status="unavailable", username=username)

    _write_cache(_fresh_key(username), profile, _FRESH_TTL_SECONDS)
    if profile.status == "ok":
        _write_cache(_last_good_key(username), profile, _LAST_GOOD_TTL_SECONDS)
    return profile
