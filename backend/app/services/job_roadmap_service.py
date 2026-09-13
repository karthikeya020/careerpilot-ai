"""Deterministic "how to crack this dream job" roadmap.

Built from the role's sector, seniority and required skills -- no LLM call,
no invented numbers. The framing is deliberately hard: the point is that a
student sees the real bar and the real amount of work, then has a concrete
week-by-week plan (wired to Assessment, Interview Arena and GraphRAG) to
close it.
"""

from app.schemas.job_roadmap import JobRoadmapOut, RoadmapAction, RoadmapPhase

_SENIOR_HINTS = ("senior", "staff", "lead", "principal", "mid", "ii", "iii")
_JUNIOR_HINTS = ("intern", "new grad", "new-grad", "university", "graduate", "trainee", "associate", "i ")

_DIFFICULTY_BY_SECTOR = {
    "faang": "brutal",
    "research": "brutal",
    "finance": "hard",
    "startup": "hard",
    "consulting": "achievable",
    "government": "achievable",
}

_SECTOR_BAR = {
    "faang": (
        "5-6 rounds and a hiring-committee review. Offer rates sit around 1-3%. They expect the "
        "optimal solution, coded cleanly and tested, in ~35 minutes -- plus a system-design round and a "
        "behavioural bar-raiser that can sink an otherwise strong loop."
    ),
    "research": (
        "A publications / open-source bar on top of strong engineering. Expect a research-depth screen, a "
        "coding round, and a discussion of your own projects where hand-waving is fatal."
    ),
    "finance": (
        "4-5 rounds, heavy on data structures under time pressure, low-latency / concurrency questions, and "
        "a values interview. Precision and correctness are weighted over cleverness."
    ),
    "startup": (
        "3-4 rounds but a very high slope: a take-home or pair-programming session on real code, a system "
        "design / product-sense round, and strong signal expected on ownership and shipping speed."
    ),
    "consulting": (
        "Aptitude + a structured technical round + case/behavioural interviews. Communication and structured "
        "problem-solving are scored as heavily as the code."
    ),
    "government": (
        "A written exam (quant + reasoning + CS core) is the real filter, followed by a technical + HR "
        "interview. Consistency across the whole syllabus beats depth in one area."
    ),
}

_COMPANY_BAR = {
    "Google": "Google: 4-5 onsite rounds, ~35 min each, optimal + clean + tested code expected, one system-design round, 'Googleyness' behavioural. Hiring committee can still say no after a strong loop.",
    "Stripe": "Stripe: an integration/bug-squash round on real-ish code, an API/systems design round, a debugging round, and a values interview. They test whether you can ship, not just whiteboard.",
    "Databricks": "Databricks: hard DSA (often Hard-tier), a distributed-systems design round, and deep dives on concurrency and big-data internals.",
    "Anthropic": "Anthropic: strong coding bar plus genuine interest in safety/alignment. Expect to reason carefully about edge cases and to discuss trade-offs, not just pass tests.",
    "Amazon": "Amazon: every round maps to Leadership Principles -- prepare 2 STAR stories per principle. Two coding rounds, one system design, one bar-raiser.",
}


def _seniority_of(title: str, explicit: str | None) -> str:
    t = f" {title.lower()} "
    if explicit and explicit not in ("", "entry_level"):
        return explicit
    if any(h in t for h in _JUNIOR_HINTS):
        return "entry_level"
    if any(h in t for h in _SENIOR_HINTS):
        return "mid_level"
    return "entry_level"


# skill -> a concrete build action + where to practise it
_SKILL_ACTION: dict[str, tuple[str, str | None]] = {
    "Data Structures": ("Re-implement every core structure from scratch (dynamic array, linked list, hash map, heap, trie, union-find, balanced BST).", "/assessment"),
    "Algorithms": ("Drill the 14 patterns (two pointers, sliding window, BFS/DFS, backtracking, binary search on answer, top-k heap, DP on subsequences...).", "/assessment"),
    "System Design": ("Design and write up 8 systems end-to-end (URL shortener, news feed, rate limiter, chat, search, ride-share, object store, metrics pipeline).", "/graphrag"),
    "Python": ("Build a non-trivial CLI or service in idiomatic Python: type hints, generators, context managers, tests, packaging.", "https://leetcode.com/problemset/?topicSlugs=python"),
    "Java": ("Build a concurrent service in Java: the collections framework, the memory model, ExecutorService, and the equals/hashCode contract.", "https://leetcode.com/problemset/concurrency/"),
    "JavaScript": ("Build an app with no framework first: closures, the event loop, promises, and DOM APIs, then add a framework.", "https://leetcode.com/problemset/?topicSlugs=javascript"),
    "TypeScript": ("Convert a real JS project to strict TypeScript -- generics, discriminated unions, and utility types.", None),
    "React": ("Build 3 non-toy React apps: data fetching, forms, virtualised lists, and state management without a library.", None),
    "SQL": ("Solve LeetCode's SQL track and design + query a normalised schema for a real domain.", "https://leetcode.com/studyplan/top-sql-50/"),
    "PostgreSQL": ("Learn indexes, EXPLAIN ANALYZE, transactions and isolation levels on a dataset with millions of rows.", None),
    "AWS": ("Deploy a real service: VPC, ECS/Lambda, RDS, S3, IAM least-privilege, and infra-as-code.", None),
    "Docker": ("Containerise a multi-service app and write a Compose file; understand layers, caching and image size.", None),
    "Kubernetes": ("Run the app on a local cluster: deployments, services, config/secrets, probes, and an ingress.", None),
    "Machine Learning": ("Train, evaluate and ship one model end-to-end with a proper train/val/test split and error analysis.", None),
    "Deep Learning": ("Implement a small transformer or CNN from scratch in PyTorch, then reproduce a paper's result.", None),
    "REST APIs": ("Design and build a versioned REST API with auth, pagination, idempotency and an OpenAPI spec.", None),
    "GraphQL": ("Build a GraphQL API with a schema, resolvers, dataloaders (N+1), and auth.", None),
    "Testing": ("Get a real project to 80%+ meaningful coverage: unit, integration, and one end-to-end suite.", None),
    "CI/CD": ("Set up a pipeline that lints, tests, builds, and deploys on every push, with a rollback path.", None),
}

_DEFAULT_SKILL_ACTION = ("Build one real project that forces you to use it under pressure, then get it reviewed.", None)


def _problem_budget(difficulty: str) -> tuple[int, str]:
    if difficulty == "brutal":
        return 250, "~100 medium (arrays/strings, hashing, two pointers), ~70 trees & graphs, ~50 DP, ~30 hard"
    if difficulty == "hard":
        return 150, "~70 medium, ~40 trees & graphs, ~25 DP, ~15 hard"
    return 80, "~50 easy-medium across all patterns, ~20 medium graphs/DP, ~10 hard"


def build_roadmap(
    company: str,
    title: str,
    sector: str,
    seniority: str | None,
    skills: list[str],
) -> JobRoadmapOut:
    sector = sector if sector in _DIFFICULTY_BY_SECTOR else "startup"
    difficulty = _DIFFICULTY_BY_SECTOR[sector]
    seniority_norm = _seniority_of(title, seniority)
    bar = _COMPANY_BAR.get(company) or _SECTOR_BAR[sector]

    skills_focus = []
    for s in skills:
        if s not in skills_focus:
            skills_focus.append(s)
    core_skills = skills_focus[:8] or ["Data Structures", "Algorithms", "System Design"]

    problem_count, problem_mix = _problem_budget(difficulty)
    needs_system_design = sector in ("faang", "startup", "finance") or seniority_norm != "entry_level"

    phases: list[RoadmapPhase] = []

    phases.append(
        RoadmapPhase(
            title="Foundations",
            weeks="Weeks 1-4",
            why="Everything downstream assumes fluency in one language and the core data structures. Fix this first or every later phase is slower.",
            actions=[
                RoadmapAction(text="Take the CareerPilot assessments for DSA, and your primary language, until every concept is above 70%.", link="/assessment"),
                RoadmapAction(text="Re-implement array, linked list, stack/queue, hash map, heap, and binary tree from scratch with tests."),
                RoadmapAction(text="Set a daily-goal in Assessment tied to this company so 5 targeted questions land every day.", link="/assessment"),
            ],
            milestone="No assessment concept below 70%; you can code the core structures from memory.",
        )
    )

    role_actions = []
    for skill in core_skills:
        text, link = _SKILL_ACTION.get(skill, _DEFAULT_SKILL_ACTION)
        role_actions.append(RoadmapAction(text=f"{skill}: {text}", link=link))
    phases.append(
        RoadmapPhase(
            title="Role-specific skills",
            weeks="Weeks 3-10",
            why=f"{company} screens hard on the skills in this exact JD. Surface-level familiarity fails the technical rounds -- you need shipped evidence.",
            actions=role_actions,
            milestone="Each JD skill is backed by a real project or a passed assessment, not a bullet point.",
        )
    )

    phases.append(
        RoadmapPhase(
            title="Problem-solving depth",
            weeks="Weeks 6-16",
            why=f"The coding rounds are pattern recognition under a clock. {problem_count} deliberate problems is the realistic volume for this bar.",
            actions=[
                RoadmapAction(text=f"Work ~{problem_count} problems, spread as: {problem_mix}. Redo any you couldn't solve in 25 minutes.", link="https://leetcode.com/studyplan/leetcode-75/"),
                RoadmapAction(text="Use the LeetCode practice plan on the Assessment page -- it targets the concepts your assessments show you are weakest on.", link="/assessment"),
                RoadmapAction(text="Every problem: state the brute force and its Big-O out loud, then the optimal, before coding. Explain your solution in the Assessment 'explain how you solved' pop-up.", link="/assessment"),
            ],
            milestone="You can go from cold problem to a clean, tested optimal solution in <30 minutes, talking the whole time.",
        )
    )

    if needs_system_design:
        phases.append(
            RoadmapPhase(
                title="System design",
                weeks="Weeks 10-18",
                why="At this bar there is a dedicated design round. Hand-waving on load estimation, data modelling, or failure modes is an instant no.",
                actions=[
                    RoadmapAction(text="Design 8 systems end-to-end with numbers: capacity estimate, API, data model, scaling path, and failure handling."),
                    RoadmapAction(text="Practise explaining a design in 40 minutes on a whiteboard, out loud, handling follow-ups."),
                    RoadmapAction(text="Use GraphRAG to trace how your weak concepts connect so gaps in fundamentals don't surface mid-round.", link="/graphrag"),
                ],
                milestone="You can drive a 40-minute design round for any of the 8 systems, unprompted.",
            )
        )

    loop_note = _COMPANY_BAR.get(company) or f"the {sector} interview loop"
    phases.append(
        RoadmapPhase(
            title=f"{company} interview loop",
            weeks="Weeks 14-20",
            why=f"Generic prep gets you to the door. This phase is about {company} specifically: {loop_note}",
            actions=[
                RoadmapAction(text=f"Study {company}'s engineering blog and recent tech talks; know their stack and one hard problem they've written about."),
                RoadmapAction(text="Write 8-10 STAR stories (conflict, failure, leadership, ambiguity, impact) and rehearse them to 90 seconds each."),
                RoadmapAction(text="Map every past-round theme you can find for this company/role to a prep task and close it."),
            ],
            milestone=f"You can name {company}'s round structure and have a rehearsed answer for every behavioural theme.",
        )
    )

    mock_rounds = 8 if difficulty == "brutal" else 6 if difficulty == "hard" else 4
    phases.append(
        RoadmapPhase(
            title="Hard mock loop & apply",
            weeks="Weeks 18-24",
            why="The last gap is performance under real pressure. Simulate the actual loop before it counts.",
            actions=[
                RoadmapAction(text=f"Run {mock_rounds} timed mock interviews in Interview Arena at Hard difficulty -- 35-minute clock, camera on, no hints. Review every transcript.", link="/interview"),
                RoadmapAction(text="Get 2 referrals (alumni, LinkedIn, ex-colleagues). A referral roughly doubles your callback rate at this bar."),
                RoadmapAction(text="Apply in a batch, front-load your top choice, and prepare your compensation numbers before the first call."),
            ],
            milestone=f"{mock_rounds} Hard mock rounds done and reviewed; applications in; you are calm on the clock.",
        )
    )

    total_weeks = 24 if needs_system_design else 22
    if difficulty == "achievable":
        total_weeks = 16
    difficulty_word = {"brutal": "brutal", "hard": "hard but very doable", "achievable": "achievable with steady work"}[difficulty]
    summary = (
        f"Cracking {title} at {company} is {difficulty_word}. Plan on roughly {total_weeks} weeks of focused "
        f"effort across {len(phases)} phases: foundations, the {len(core_skills)} skills in this JD, "
        f"~{problem_count} deliberate problems, "
        + ("a real system-design round, " if needs_system_design else "")
        + f"{company}-specific prep, and {mock_rounds} hard mock interviews before you apply."
    )

    return JobRoadmapOut(
        company=company,
        title=title,
        sector=sector,
        seniority=seniority_norm,
        difficulty=difficulty,
        bar=bar,
        total_weeks=total_weeks,
        summary=summary,
        skills_focus=core_skills,
        phases=phases,
    )
