# Final Stage Script — Seven-Minute Standard Slot

This is the primary, word-for-word script for the competition stage. Every
number in it was pulled live from the running application on 2026-08-05
immediately after a full demo reset (`docker compose restart backend`) —
see "Numbers will drift slightly" below. `THREE_MINUTE_DEMO.md` and
`TWELVE_MINUTE_DEMO.md` are compressions/expansions of this same script.
`SEVEN_MINUTE_DEMO.md` is the short table-form summary of this file.

## Before you walk on stage

1. `docker compose restart backend` — one-click reset. Wait ~15s, confirm
   `docker compose ps` shows all 5 healthy.
2. **Two browser tabs, both logged in as** `demo.student@careerpilot.ai` /
   `DemoPass!2026`, **both fullscreen-capable**:
   - **Tab A** — navigate to `/competition`, press `F` for fullscreen. This
     is your main driver for almost the entire talk.
   - **Tab B** — pre-load the real Interview Replay page. The app has no
     in-nav "past interviews" list (a known gap, see `PRESENTATION_DAY_
     RUNBOOK.md` "Known rough edges"), so grab the current session ID once
     right after your reset:
     ```
     docker compose exec postgres psql -U careerpilot -d careerpilot -t -c "SELECT id FROM interview_sessions;"
     ```
     Open `http://localhost:3000/interview/<that-id>/replay` in Tab B and
     leave it sitting there, scrolled to the top.
3. Rehearse the exact alt-tab motion (`Alt+Tab` or click the taskbar) you'll
   use twice — see 2:50 and 3:45 below. Tab A's Competition Mode state is
   per-tab and does **not** reset when you switch away and back.
4. Notifications off, other apps closed, laptop plugged in. See
   `PROJECTOR_CHECKLIST.md`.

**Numbers will drift slightly between resets** — the seed re-runs live
agent code every time, not a fixed script, so an interview answer's
confidence might land at 63% one run and 61% the next. The *shape* of every
number below (which one is biggest, which is honestly low, which is a
perfect score) is stable and is what the narration leans on — read the
number on screen, don't force-fit the one printed here if it's drifted a
point or two.

---

## 0:00–0:30 — Hook and problem (30s)

**Screen**: Tab A, `/competition`, step 1/14 "Opening" (already loaded,
fullscreen, before you start talking).

**Click sequence**: none yet — let the animated orb sit still while you
open verbally.

**Spoken words** (audience-facing):
> "Every one of you has used a career tool that gives you a score with no
> explanation. A resume grader. A generic chatbot telling you you're
> '75% ready.' Ready for what? Based on what evidence? Nobody can tell you.
> CareerPilot AI is the Career Operating System that shows its work — every
> number traced to real evidence, every recommendation explained, nothing
> invented."

**Technical-judge aside** (skip for the general-audience pass): "Nothing
you'll see for the next seven minutes is pre-recorded or mocked — this is
the actual product, running locally, no internet dependency."

**Transition**: press `→` (Right) at 0:28 to land on step 2 exactly as you
finish the sentence.

---

## 0:30–1:20 — Career Twin Awakening (50s)

**Screen**: Tab A, steps 2 → 3.

**Click sequence**:
- `→` (already done at end of hook) → step 2/14 "Meet the Student"
- Narrate ~8s
- `→` → step 3/14 "Career Twin Awakening"
- Narrate ~40s

**Spoken words** — step 2 (~8s):
> "Meet Aanya — a real seeded student account, targeting a Backend
> Engineering Intern role. Everything from here is her real, stored data."

**Spoken words** — step 3 (~40s):
> "This is her Career Twin — a persistent model of six readiness
> components, versioned every time new evidence arrives. Right now: 73%
> overall, but look — 36% confidence. The system is telling you, honestly,
> that it isn't fully sure yet. [point] Portfolio readiness sits at 59%
> with only one evidence item — flagged low-sample, not padded to look
> more established than it is. That's Constitution rule one in this
> product: every score comes from stored evidence, or it says
> 'insufficient evidence.' Never a fabricated number."

**Technical-judge aside**: "Formula version `twin-v2` — evidence-diversity
weighting and Bayesian shrinkage toward a neutral prior below 3 evidence
items or 2 independent sources. That safeguard exists because an earlier
internal test showed a single strong interview reading as a confidently
established skill — we caught it and fixed it before this build."

**Transition**: `→` at ~1:18.

---

## 1:20–2:10 — GraphRAG root-cause reveal (50s)

**Screen**: Tab A, steps 4 → 5.

**Click sequence**:
- step 4/14 "Priority Weakness" — narrate ~10s
- `→` → step 5/14 "GraphRAG Root Cause" — narrate ~40s

**Spoken words** — step 4 (~10s):
> "Every Twin has a priority weakness. For Aanya right now it's portfolio
> readiness — missing FastAPI evidence. But *why* does the system flag
> that, and not something else? That's the next screen."

**Spoken words** — step 5 (~40s), narrate the graph chain from memory —
this exact chain is the real, stored trace for this account's first
detected gap:
> "Here's an earlier example from her account of how CareerPilot finds a
> root cause — not a guess, a graph traversal. She answered a SQL question
> wrong. The system doesn't just say 'wrong, try again.' It walks a real
> stored dependency graph: the question tests the concept Inner Join.
> Inner Join depends on Joins. Joins depends on Table Relationships. Table
> Relationships depends on the Relational Model. And her target role,
> Backend Engineering Intern, requires Inner Join. That entire chain is
> traversed through a real Neo4j graph — you can see the badge: 'Graph
> retrieval used,' 60% confidence, honestly stated, not inflated."

**Technical-judge aside** (toggle "Technical view" top-right if there's
time, ~5s): "Route: single agent. Agents invoked: graphrag, career_coach.
If Neo4j goes down mid-session, this same query falls back to the
identical relational data — we verified that live by killing the Neo4j
container mid-demo in an earlier pass, and it never crashed."

**Transition**: `→` at ~2:08.

---

## 2:10–2:50 — CARE routing and mission (40s)

**Screen**: Tab A, steps 6 → 7.

**Click sequence**:
- step 6/14 "CARE Decision" — narrate ~15s
- `→` → step 7/14 "Today's Mission" — narrate ~25s

**Spoken words** — step 6 (~15s):
> "Every AI-assisted decision in this product goes through CARE — Confidence-
> Aware Reasoning Engine. It decides, per decision, whether one specialist
> is enough or a whole council needs to weigh in. Here, evidence was
> strong enough that one specialist settled it at 72% confidence — CARE
> didn't waste a council on an easy case. When evidence conflicts, it
> escalates instead — I'll show you the proof of that adaptivity in a
> moment, in our research numbers."

**Spoken words** — step 7 (~25s):
> "And the loop closes here: 'Strengthen FastAPI' — a mission generated
> directly from that weak evidence, with a concrete task, not generic
> advice. This is CareerPilot's autonomous loop: observe evidence,
> diagnose the gap, plan a mission, and when the student acts, reassess and
> update the Twin. Nothing here is a static curriculum — it's generated
> from *her* evidence."

**Transition**: `→` at ~2:48.

---

## 2:50–3:45 — Interview Replay (55s)

**Screen**: Tab A steps 8 → 9, then **switch to Tab B**.

**Click sequence**:
- step 8/14 "Career Twin Update" — narrate ~8s (bridge line)
- `→` → step 9/14 "Interview Intelligence" — narrate ~12s
- **Alt+Tab to Tab B** (pre-loaded Interview Replay) — narrate ~30s,
  scroll down one question to the technical question
- **Alt+Tab back to Tab A** — ~5s, arrives back on step 9 unchanged

**Spoken words** — step 8 (~8s):
> "And you can already see the Twin move — up nearly 7 and a half points
> after her last mock interview. Let's go inside that interview."

**Spoken words** — step 9 (~12s):
> "CARE routed this answer to a single specialist — relevance, correctness,
> structure, communication, and a check against her actual resume — all
> real evaluation, not a canned rubric."

**Spoken words** — switch to Tab B, real Interview Replay (~30s):
> "This is the real replay screen — full transcript, not a summary.
> [scroll to the technical question, "What is a Python list comprehension"]
> Look at this one: every dimension — depth, clarity, relevance,
> conciseness, correctness, communication — scored, and this particular
> answer nailed all six. No generic 'good job' — real per-dimension
> feedback, and where an earlier answer was weaker [point at the HR
> question above], it tells her exactly which STAR component was missing,
> with a framework for how to fix it next time."

**Transition**: Alt+Tab back to Tab A at ~3:43.

---

## 3:45–4:50 — Career Experiment Lab (65s)

**Screen**: Tab A step 10, then **switch to Tab B**, navigate sidebar to
Experiment Lab, run a scenario live.

**Click sequence**:
- step 10/14 "Career Experiment Lab" (Tab A) — narrate ~10s
- **Alt+Tab to Tab B**
- Click "Experiment Lab" in the left sidebar
- Click **"Run scenario"** (form is already pre-filled: SQL / practice
  problems / 20 hours — no typing needed) — result appears in 1–3s
- Narrate the live result ~40s
- **Alt+Tab back to Tab A** ~10s

**Spoken words** — step 10 (~10s):
> "She already has real experiments on file — a balanced 30-hour plan
> projects a jump from 73% to just over 75%. But watch — I'm going to run
> a brand new one, live, right now."

**Spoken words** — running live in Tab B (~40s):
> "[click Run scenario] That's not a loading spinner for an API call to
> some model — that result just came from a fully deterministic simulation
> engine. No LLM decides these numbers; a versioned formula does —
> diminishing returns on hours invested, evidence diversity, her own
> historical trend, and her actual job description's stated requirements.
> [point at the disclaimer text] And it says so, right on the card:
> 'personalized scenario estimate — not a guaranteed outcome or hiring
> prediction.' We do not let this product predict whether she gets hired.
> Ever."

**Transition**: Alt+Tab back to Tab A at ~4:48.

---

## 4:50–5:40 — Research proof (50s)

**Screen**: Tab A step 11, then **switch to Tab B**, navigate to Research
Lab, run the ablation suite live.

**Click sequence**:
- step 11/14 "Research Proof" (Tab A) — narrate ~10s
- **Alt+Tab to Tab B**
- Click "Research Lab" in the left sidebar
- Click **"Run all 6 ablations"** — real numbers populate in a few seconds
- Narrate ~35s
- **Alt+Tab back to Tab A** ~5s

**Spoken words** — step 11 (~10s):
> "Why is this better than a chatbot with a system prompt about careers?
> We don't just claim it — we measure it. Let me run our full research
> suite live."

**Spoken words** — running live in Tab B (~35s):
> "[click Run all 6 ablations] Six real ablations, run against the actual
> production agents, not a slide. CARE's adaptive routing matches expert
> judgment 100% of the time on our test cases — a fixed single-agent
> approach only gets 12.5%. Graph traversal for root-cause finding: 100%
> accurate by construction, because it follows a real stored dependency —
> pure vector similarity search, the same approach a generic RAG chatbot
> uses, only finds the right prerequisite half the time. And — we don't
> hide the results that don't flatter us: one of our six ablations found a
> real limitation in how our memory agent scores confidence, and we
> disclosed it instead of hiding it. That's what a real ablation study
> looks like."

**Transition**: Alt+Tab back to Tab A at ~5:38.

---

## 5:40–6:15 — Responsible AI and institutional value (35s)

**Screen**: Tab A, steps 12 → 13.

**Click sequence**:
- step 12/14 "Responsible AI" — narrate ~18s
- `→` → step 13/14 "Institutional Scale" — narrate ~17s

**Spoken words** — step 12 (~18s):
> "And here's what this system will never do, on the record: no hiring
> probability, ever computed or shown. No lie detection. No public ranking
> of students. No inferred emotional or psychological state. Full student
> control — export everything, delete the audio, delete the account."

**Spoken words** — step 13 (~17s):
> "The same evidence model scales past one student — faculty see cohort
> skill gaps, placement sees readiness distribution, recruiters see only
> students who explicitly opt in, and never a ranking. One honest note:
> our demo database has one real student in it today, so these dashboards
> show a cohort of one — the aggregation logic is real and tested, the
> cohort just isn't populated yet for this stage."

**Transition**: `→` at ~6:13.

---

## 6:15–7:00 — Closing (45s)

**Screen**: Tab A, step 14/14 "Closing".

**Click sequence**: arrive on step 14, no further clicks. Optionally press
`Esc` at the very end to exit cleanly to `/dashboard` in front of the
judges, proving it's a real logged-in session, not a slide deck.

**Spoken words** (~45s):
> "Past. Present. Simulated future. CareerPilot AI doesn't prepare a
> student for one interview — it continuously learns how to guide every
> student toward their strongest possible career, and it never has to lie
> to do it. Every score traced to evidence. Every recommendation
> explained. Every claim we just showed you, backed by a number you can
> re-run yourself, right now, on this laptop, with no internet connection
> and no paid API key. CareerPilot AI — your career, continuously
> evolving. Thank you."

**End state**: step 14/14, or `/dashboard` if you pressed `Esc`. Either is
a clean, intentional stopping point for Q&A.

---

## If you're running long or short

- **30s over by 3:45**: skip the Tab B alt-tab for Interview Replay
  entirely and narrate step 9's summary only — costs you the single
  strongest "real, not staged" visual proof, so only cut it as a last
  resort.
- **60s over by 4:50**: skip the live "Run scenario" click in Experiment
  Lab and narrate the pre-seeded "Balanced 30h" card in step 10 instead —
  still real data, just not clicked live.
- **Ahead of schedule**: linger on the GraphRAG chain (1:20–2:10) — it's
  the highest-density technical proof point and audiences ask about it
  most in Q&A, so extra seconds there pay off.
- **A screen shows an unexpected empty state**: see `PRESENTATION_DAY_
  RUNBOOK.md` "If something breaks live" — do not panic-click; every
  empty state in this product is an honest one, never a crash.
