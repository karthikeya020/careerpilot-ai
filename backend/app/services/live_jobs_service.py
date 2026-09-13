"""Live job feed -- real, currently-open roles pulled from companies' own
official public job-board APIs (Greenhouse and Lever). These are the same
JSON endpoints the companies use to render their own careers pages, so this
is not scraping: it's their published feed.

Same fail-open, two-tier Redis caching posture as
app/services/github_profile_service.py:
  - a short "fresh" cache (6h) per company board;
  - a long "last known good" cache (7d), only written from a successful
    fetch, so a board being briefly down doesn't blank the feed.
If a board is unreachable and nothing is cached, that company is simply
skipped. If *every* board fails, the feed falls back to the curated
company_job_catalog listings so Job Match is never empty.

Skills are extracted from the JD text against the same skill taxonomy the
rest of the app scores against -- with an importance tag (core / strong /
familiar) inferred from where in the JD the skill appears.
"""

import html
import logging
import re
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.redis_client import get_redis
from app.models.job_catalog import CompanyJobListing
from app.schemas.live_jobs import LiveJobOut, LiveJobSkillOut

logger = logging.getLogger("careerpilot")

_FRESH_TTL = 60 * 60 * 6
_LAST_GOOD_TTL = 60 * 60 * 24 * 7
_FEED_TTL = 60 * 60
_TIMEOUT = 8.0
_PER_COMPANY_CAP = 12

# (source, board_token, display company, sector). Curated -- every token here
# is a real, public Greenhouse/Lever board.
COMPANY_BOARDS: list[tuple[str, str, str, str]] = [
    ("greenhouse", "stripe", "Stripe", "startup"),
    ("greenhouse", "figma", "Figma", "startup"),
    ("greenhouse", "notion", "Notion", "startup"),
    ("greenhouse", "databricks", "Databricks", "startup"),
    ("greenhouse", "airtable", "Airtable", "startup"),
    ("greenhouse", "ramp", "Ramp", "finance"),
    ("greenhouse", "brex", "Brex", "finance"),
    ("greenhouse", "plaid", "Plaid", "finance"),
    ("greenhouse", "gitlab", "GitLab", "startup"),
    ("greenhouse", "dropbox", "Dropbox", "faang"),
    ("greenhouse", "coinbase", "Coinbase", "finance"),
    ("greenhouse", "robinhood", "Robinhood", "finance"),
    ("greenhouse", "discord", "Discord", "startup"),
    ("greenhouse", "retool", "Retool", "startup"),
    ("greenhouse", "samsara", "Samsara", "startup"),
    ("greenhouse", "benchling", "Benchling", "research"),
    ("greenhouse", "cloudflare", "Cloudflare", "startup"),
    ("greenhouse", "instacart", "Instacart", "startup"),
    ("greenhouse", "affirm", "Affirm", "finance"),
    ("greenhouse", "sofi", "SoFi", "finance"),
    ("lever", "netlify", "Netlify", "startup"),
    ("lever", "mixpanel", "Mixpanel", "startup"),
    ("lever", "voleon", "The Voleon Group", "finance"),
    ("lever", "attentive", "Attentive", "startup"),
    # ---- India-headquartered / India-heavy boards (best effort; a wrong
    # token just 404s and is skipped fail-open) ----
    ("greenhouse", "postman", "Postman", "startup"),
    ("greenhouse", "hasura", "Hasura", "startup"),
    ("greenhouse", "innovaccer", "Innovaccer", "startup"),
    ("greenhouse", "sprinklr", "Sprinklr", "startup"),
    ("greenhouse", "chargebee", "Chargebee", "startup"),
    ("greenhouse", "mindtickle", "Mindtickle", "startup"),
    ("greenhouse", "whatfix", "Whatfix", "startup"),
    ("greenhouse", "druva", "Druva", "startup"),
    ("lever", "razorpay", "Razorpay", "finance"),
    ("lever", "atlan", "Atlan", "startup"),
]

_ENG_TITLE_RE = re.compile(
    r"\b(software engineer|software developer|engineer(?:ing)?|developer|sde|swe|"
    r"programmer|data scientist|machine learning|ml engineer|research engineer|"
    r"full[\s-]?stack|front[\s-]?end|back[\s-]?end|devops|site reliability|sre|"
    r"intern(?:ship)?|co-?op|apprentice|graduate trainee)\b",
    re.I,
)

_INTERN_RE = re.compile(
    r"\b(intern(?:ship)?|co-?op|apprentice(?:ship)?|trainee|working student|summer 20\d\d)\b",
    re.I,
)
# titles that contain an eng-ish word but are not what a CS student prepares for
_NON_ENG_RE = re.compile(
    r"\b(account executive|solutions? (architect|engineer|consultant)|sales|"
    r"recruit|marketing|counsel|partnerships?|customer success|support engineer|"
    r"technical writer|program manager|product manager|designer|analyst relations)\b",
    re.I,
)

# canonical skill -> keyword patterns (word-boundary, case-insensitive)
_SKILL_KEYWORDS: dict[str, list[str]] = {
    "Python": [r"python"],
    "Java": [r"\bjava\b"],
    "JavaScript": [r"javascript", r"\bjs\b"],
    "TypeScript": [r"typescript", r"\bts\b"],
    "C++": [r"c\+\+"],
    "Go": [r"\bgolang\b", r"\bgo\b(?= programming| lang| services| microservices)"],
    "SQL": [r"\bsql\b", r"postgres", r"mysql"],
    "React": [r"react(?:\.js)?"],
    "Next.js": [r"next\.js", r"nextjs"],
    "Node.js": [r"node\.?js"],
    "GraphQL": [r"graphql"],
    "REST APIs": [r"rest(?:ful)? api", r"\brest\b"],
    "Data Structures": [r"data structures"],
    "Algorithms": [r"algorithms?"],
    "System Design": [r"system design", r"distributed systems", r"scalab"],
    "PostgreSQL": [r"postgres(?:ql)?"],
    "MongoDB": [r"mongo"],
    "Redis": [r"\bredis\b"],
    "Docker": [r"docker", r"container"],
    "Kubernetes": [r"kubernetes", r"\bk8s\b"],
    "AWS": [r"\baws\b", r"amazon web services"],
    "Azure": [r"\bazure\b"],
    "Google Cloud Platform": [r"\bgcp\b", r"google cloud"],
    "CI/CD": [r"ci/cd", r"continuous (?:integration|delivery|deployment)"],
    "Testing": [r"unit test", r"integration test", r"test coverage", r"\btdd\b"],
    "Machine Learning": [r"machine learning", r"\bml\b"],
    "Deep Learning": [r"deep learning", r"neural network"],
    "PyTorch": [r"pytorch"],
    "TensorFlow": [r"tensorflow"],
    "Data Analysis": [r"data analysis", r"analytics"],
    "Pandas": [r"pandas"],
    "Linux": [r"\blinux\b", r"unix"],
    "Git": [r"\bgit\b", r"version control"],
    "Communication": [r"communication skills", r"communicate (?:clearly|effectively)"],
    "Agile/Scrum": [r"agile", r"scrum"],
}

_NICE_TO_HAVE_MARKERS = ("nice to have", "bonus", "plus", "preferred", "a plus", "nice-to-have")
_MUST_MARKERS = ("required", "must have", "must-have", "you have", "we require", "requirements")


# ---------------------------------------------------------------- fetch layer


def _fresh_key(source: str, token: str) -> str:
    return f"live_jobs:fresh:{source}:{token}"


def _last_good_key(source: str, token: str) -> str:
    return f"live_jobs:last_good:{source}:{token}"


def _read_cache(key: str) -> list[dict] | None:
    try:
        raw = get_redis().get(key)
    except Exception:
        return None
    if not raw:
        return None
    try:
        import json

        return json.loads(raw)
    except Exception:
        return None


def _write_cache(key: str, jobs: list[dict], ttl: int) -> None:
    try:
        import json

        get_redis().set(key, json.dumps(jobs), ex=ttl)
    except Exception:
        logger.warning("live_jobs cache write failed for %s", key)


def _strip_html(raw: str) -> str:
    text = html.unescape(raw or "")
    text = re.sub(r"<(li|p|br|/tr|/h[1-6])[^>]*>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _fetch_greenhouse(token: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    with httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": "CareerPilotAI"}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
    out = []
    for job in data.get("jobs", []):
        out.append(
            {
                "ext_id": str(job.get("id")),
                "title": job.get("title", "").strip(),
                "location": (job.get("location") or {}).get("name"),
                "url": job.get("absolute_url"),
                "posted_at": job.get("updated_at"),
                "team": next((d.get("name") for d in job.get("departments", []) if d.get("name")), None),
                "text": _strip_html(job.get("content", "")),
            }
        )
    return out


def _fetch_lever(token: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{token}?mode=json"
    with httpx.Client(timeout=_TIMEOUT, headers={"User-Agent": "CareerPilotAI"}) as client:
        resp = client.get(url)
        resp.raise_for_status()
        data = resp.json()
    out = []
    for job in data if isinstance(data, list) else []:
        cats = job.get("categories") or {}
        lists_text = "\n".join(
            f"{blk.get('text', '')}\n{_strip_html(blk.get('content', ''))}" for blk in job.get("lists", [])
        )
        body = (job.get("descriptionPlain") or _strip_html(job.get("description", ""))) + "\n\n" + lists_text
        created = job.get("createdAt")
        posted = (
            datetime.fromtimestamp(created / 1000, tz=timezone.utc).isoformat()
            if isinstance(created, (int, float))
            else None
        )
        out.append(
            {
                "ext_id": str(job.get("id")),
                "title": (job.get("text") or "").strip(),
                "location": cats.get("location"),
                "url": job.get("hostedUrl") or job.get("applyUrl"),
                "posted_at": posted,
                "team": cats.get("team") or cats.get("department"),
                "text": body.strip(),
            }
        )
    return out


def _fetch_board(source: str, token: str) -> list[dict] | None:
    fresh = _read_cache(_fresh_key(source, token))
    if fresh is not None:
        return fresh
    try:
        jobs = _fetch_greenhouse(token) if source == "greenhouse" else _fetch_lever(token)
    except (httpx.HTTPError, ValueError, KeyError, TypeError):
        return _read_cache(_last_good_key(source, token))
    jobs = [
        j
        for j in jobs
        if j["title"] and _ENG_TITLE_RE.search(j["title"]) and not _NON_ENG_RE.search(j["title"])
    ][:_PER_COMPANY_CAP]
    _write_cache(_fresh_key(source, token), jobs, _FRESH_TTL)
    if jobs:
        _write_cache(_last_good_key(source, token), jobs, _LAST_GOOD_TTL)
    return jobs


# ------------------------------------------------------------- normalisation


def _sections(text: str) -> dict[str, list[str]]:
    """Split a JD into bullet lists keyed by a normalised header."""
    header_re = re.compile(
        r"^\s*(what you'?ll do|responsibilities|what you will do|the role|"
        r"what we'?re looking for|requirements|qualifications|you have|about you|"
        r"nice to have|bonus points|preferred)\s*:?\s*$",
        re.I,
    )
    sections: dict[str, list[str]] = {}
    current = "body"
    for line in text.splitlines():
        stripped = line.strip(" \t•-–*")
        if not stripped:
            continue
        if header_re.match(line.strip()):
            current = line.strip().lower().rstrip(":")
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(stripped)
    return sections


def _pick(sections: dict[str, list[str]], *keys: str) -> list[str]:
    for key in keys:
        for header, items in sections.items():
            if key in header:
                return [i for i in items if 12 <= len(i) <= 240][:8]
    return []


def _extract_skills(text: str) -> list[LiveJobSkillOut]:
    lower = text.lower()
    nice_span = ""
    for marker in _NICE_TO_HAVE_MARKERS:
        idx = lower.find(marker)
        if idx != -1:
            nice_span = lower[idx:]
            break
    skills: list[LiveJobSkillOut] = []
    for name, patterns in _SKILL_KEYWORDS.items():
        hits = 0
        in_nice = False
        for pat in patterns:
            for m in re.finditer(pat, lower):
                hits += 1
                if nice_span and lower.find(nice_span[:20]) != -1 and m.start() >= lower.find(nice_span[:20]):
                    in_nice = True
        if hits == 0:
            continue
        if in_nice and hits == 1:
            importance = "familiar"
        elif hits >= 3 or any(mk in lower[: lower.find(pat) + 200] for pat in patterns for mk in _MUST_MARKERS):
            importance = "core"
        elif hits >= 2:
            importance = "core"
        else:
            importance = "strong"
        skills.append(LiveJobSkillOut(name=name, importance=importance))
    order = {"core": 0, "strong": 1, "familiar": 2}
    skills.sort(key=lambda s: (order[s.importance], s.name))
    return skills[:16]


def _normalise(source: str, token: str, company: str, sector: str, raw: dict) -> LiveJobOut:
    text = raw["text"] or ""
    sections = _sections(text)
    paras = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 40]
    summary = (paras[0] if paras else text[:280]).strip()[:400]
    loc = raw.get("location") or "Location varies"
    return LiveJobOut(
        id=f"{source}:{token}:{raw['ext_id']}",
        company=company,
        title=raw["title"],
        location=loc,
        remote=bool(re.search(r"remote", loc, re.I)),
        url=raw.get("url") or "",
        sector=sector,
        source=source,
        posted_at=raw.get("posted_at"),
        team=raw.get("team"),
        summary=summary,
        description=text[:6000],
        responsibilities=_pick(sections, "what you", "responsibilities", "the role"),
        requirements=_pick(sections, "requirements", "looking for", "qualifications", "you have", "about you"),
        skills=_extract_skills(text),
        comp_note=_comp_note(text),
        is_live=True,
        is_internship=bool(_INTERN_RE.search(raw["title"])),
    )


_COMP_RE = re.compile(
    r"(\$[\d,]{3,}[kK]?(?:\s?[–-]\s?\$?[\d,]{3,}[kK]?)?|₹[\d,]+(?:\s?LPA)?|[\d.]+\s?LPA)"
)


def _comp_note(text: str) -> str | None:
    for line in text.splitlines():
        if re.search(r"compensation|salary|base pay|pay range|total comp", line, re.I):
            m = _COMP_RE.search(line)
            if m:
                return line.strip()[:180]
    m = _COMP_RE.search(text)
    return None if not m else f"Mentions {m.group(0)} in the posting."


def _catalog_fallback(db: Session) -> list[LiveJobOut]:
    jobs: list[LiveJobOut] = []
    for listing in db.scalars(select(CompanyJobListing)).all():
        core = [r.skill.name for r in listing.requirements if r.is_required]
        extra = [r.skill.name for r in listing.requirements if not r.is_required]
        jobs.append(
            LiveJobOut(
                id=f"catalog:{listing.id}",
                company=listing.company,
                title=listing.title,
                location="India / Hybrid",
                remote=False,
                url="",
                sector=listing.sector,
                source="catalog",
                posted_at=listing.created_at.isoformat() if listing.created_at else None,
                team=None,
                summary=listing.description,
                description=listing.description,
                responsibilities=[],
                requirements=[],
                skills=[LiveJobSkillOut(name=n, importance="core") for n in core]
                + [LiveJobSkillOut(name=n, importance="familiar") for n in extra],
                comp_note=f"Representative package: {listing.package_min_lpa:.0f}-{listing.package_max_lpa:.0f} LPA.",
                is_live=False,
                is_internship=bool(_INTERN_RE.search(listing.title)),
            )
        )
    return jobs


def _all_jobs(db: Session) -> tuple[list[LiveJobOut], bool]:
    """Merged, de-duplicated feed. bool = whether any live board contributed."""
    import json

    cached = _read_cache("live_jobs:feed")
    if cached is not None:
        return [LiveJobOut(**j) for j in cached["jobs"]], cached["live"]

    jobs: list[LiveJobOut] = []
    live = False
    for source, token, company, sector in COMPANY_BOARDS:
        raws = _fetch_board(source, token)
        if not raws:
            continue
        live = True
        for raw in raws:
            try:
                jobs.append(_normalise(source, token, company, sector, raw))
            except Exception:
                continue

    # Always blend in the curated catalog so Indian openings show up alongside
    # the (mostly US) live boards -- not only when every board is down.
    seen = {(j.company.lower(), j.title.lower()) for j in jobs}
    for cj in _catalog_fallback(db):
        if (cj.company.lower(), cj.title.lower()) not in seen:
            jobs.append(cj)

    # interleave companies so the reel doesn't show 12 Stripe roles in a row
    by_company: dict[str, list[LiveJobOut]] = {}
    for j in jobs:
        by_company.setdefault(j.company, []).append(j)
    interleaved: list[LiveJobOut] = []
    while any(by_company.values()):
        for company in list(by_company):
            if by_company[company]:
                interleaved.append(by_company[company].pop(0))
    jobs = interleaved

    try:
        get_redis().set(
            "live_jobs:feed",
            json.dumps({"jobs": [j.model_dump() for j in jobs], "live": live}),
            ex=_FEED_TTL,
        )
    except Exception:
        pass
    return jobs, live


def _by_kind(jobs: list[LiveJobOut], kind: str) -> list[LiveJobOut]:
    """kind: 'jobs' (no internships) | 'internships' (only) | 'all'."""
    if kind == "internships":
        return [j for j in jobs if j.is_internship]
    if kind == "jobs":
        return [j for j in jobs if not j.is_internship]
    return jobs


def get_feed(db: Session, cursor: int = 0, limit: int = 8, kind: str = "jobs") -> dict:
    jobs, live = _all_jobs(db)
    jobs = _by_kind(jobs, kind)
    total = len(jobs)
    if total == 0:
        return {"jobs": [], "next_cursor": 0, "total": 0, "live": live}
    cursor = max(0, cursor) % total
    page = jobs[cursor : cursor + limit]
    # Endless: when we run off the end, wrap so the reel loops forever.
    if len(page) < limit:
        page += jobs[: limit - len(page)]
    next_cursor = (cursor + limit) % total
    return {"jobs": page, "next_cursor": next_cursor, "total": total, "live": live}


def get_job(db: Session, job_id: str) -> LiveJobOut | None:
    jobs, _ = _all_jobs(db)
    return next((j for j in jobs if j.id == job_id), None)


_PKG_IN_NOTE_RE = re.compile(r"\$\s*([\d,]{4,})|([\d.]+)\s*LPA", re.I)


def _note_lpa(note: str | None) -> float:
    if not note:
        return 0.0
    m = _PKG_IN_NOTE_RE.search(note)
    if not m:
        return 0.0
    if m.group(2):
        try:
            return float(m.group(2))
        except ValueError:
            return 0.0
    try:
        return float(m.group(1).replace(",", "")) * 83 / 100_000
    except ValueError:
        return 0.0


def search_feed(
    db: Session,
    q: str = "",
    sector: str = "",
    location: str = "",
    remote: bool = False,
    skills: list[str] | None = None,
    min_package: float = 0.0,
    kind: str = "all",
    limit: int = 48,
) -> dict:
    """Filter the merged feed (live boards + curated India catalog)."""
    jobs, live = _all_jobs(db)
    jobs = _by_kind(jobs, kind)
    ql = q.strip().lower()
    loc = location.strip().lower()
    want_skills = {s.strip().lower() for s in (skills or []) if s.strip()}

    def keep(job: LiveJobOut) -> bool:
        if sector and job.sector != sector:
            return False
        if remote and not job.remote:
            return False
        if loc and loc not in (job.location or "").lower():
            return False
        if min_package > 0 and _note_lpa(job.comp_note) < min_package:
            return False
        if ql:
            hay = f"{job.company} {job.title} {' '.join(s.name for s in job.skills)}".lower()
            if ql not in hay:
                return False
        if want_skills:
            have = {s.name.lower() for s in job.skills}
            if not want_skills.issubset(have):
                return False
        return True

    filtered = [j for j in jobs if keep(j)]
    if ql:
        filtered.sort(key=lambda j: (ql not in j.title.lower(), ql not in j.company.lower()))
    return {"jobs": filtered[:limit], "total": len(filtered), "live": live}
