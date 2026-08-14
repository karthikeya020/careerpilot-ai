# Current Checkpoint

## TRL assessment + anti-fabrication audit (2026-08-07, this pass)

Requested: push the project's demonstrable maturity as high as honestly
possible (TRL framing) and independently verify the "no fake data"
constitution rules actually hold in every production code path, not just
the ones already covered by existing tests.

**Audit** (full-codebase search for `random`/`mock`/`fake`/`dummy`/
`placeholder`/`TODO`/hardcoded values across `backend/app/` and
`frontend/`, excluding test fixtures): no high-severity fabrication found.
The one real finding — `confidence` in `technical_agent.py`,
`assessment_agent.py`, and `hr_agent.py` was a flat constant selected only
by which code path ran (`0.55 if is_fallback else 0.85`), not derived from
the specific answer's grading quality — is fixed. New
`app/agents/confidence.py` computes confidence from real signal: rubric
richness (how many keywords/terms were available to grade against) and,
for multi-sub-score agents, sub-score agreement (a scattered read is
penalized). 7 new tests in `tests/test_agent_confidence.py` lock this in,
including that confidence now genuinely varies with input richness rather
than only the fallback/live branch. `career_coach_agent.py` and
`experiment_explainer_agent.py` were left as-is — both are prose-synthesis
agents that restate already-real numbers/facts computed elsewhere; their
confidence reflects phrasing-quality trust, a genuinely different (and
lower-stakes) claim than a grading score's confidence. `resume_rewrite_agent.py`
was also left as-is — its confidence is already conditioned on a real
input property (`has_sufficient_evidence`), not just the fallback branch.

The confidence fix changed `TechnicalAgent`'s output, which the existing
scoring-drift canary (`app/evaluation/drift_canary.py`) correctly caught
as a full-suite failure — it exists precisely to catch silent scoring
drift, and this was real (intentional) drift, not silent. Re-ran the 3
frozen canary cases through the updated agent, confirmed
`correctness_score`/`depth_score` were byte-identical to the old baseline
(that computation wasn't touched, only confidence was), and deliberately
re-froze `canary_baseline.json` (`canary-v2`, documented inline why) with
the new confidence values. This is exactly the tool doing its job, not a
regression.

**TRL assessment**: `docs/presentation/TRL_ASSESSMENT.md` (new) states the
project's real TRL — 6, not inflated — with evidence mapped to the
standard 9-level scale, an honest explanation of why it isn't TRL 7 yet
(no real operational users, single seeded demo account, no multi-tenancy/
SSO), and a concrete, mostly-non-research engineering roadmap to 7/8/9.

Verified: 262 backend tests passing (`pytest -q`, 255 prior + 7 new,
including the deliberate drift-canary re-freeze), 105 frontend tests
unaffected (no frontend files touched this pass).

## Truth-first rescue pass, part 1: resume data-integrity fix (2026-08-06, this pass)

**Start here for the next session.** A broad "truth-first rescue" review
was requested, covering ~15 phases of the product (resume versioning,
GraphRAG rebuild, a multi-domain assessment engine, deep interview NLP,
job deduplication, Experiment/Research Lab depth, actionable Trust
Center/Responsible AI controls, and a second visual pass). That full
scope is genuinely weeks of work and was not attempted end to end — see
`docs/implementation/FINAL_TRUTH_FIRST_RESCUE_PLAN.md` for the explicit
reasoning on why breadth was not faked to match the request's scale, and
`docs/implementation/FINAL_TRUTH_FIRST_DEFECT_LEDGER.md` /
`FINAL_TRUTH_FIRST_ACCEPTANCE_MATRIX.md` for the full honest per-item
status (most remaining phases are `BLOCKED`/`PARTIAL` with reasons
stated, not silently skipped).

**What this pass did fix, fully, with proof**: DEFECT-001 — resumes had
no active-version concept, so every resume ever uploaded contributed
`SkillEvidence` permanently, meaning Career Twin scores and job/JD match
coverage silently kept using evidence from resumes the student had long
since replaced. This directly violated Constitution rule 13. Fixed with
a real active/superseded resume model (migration `a3f1c9e6b2d4`), a
shared `evidence_service.get_active_skill_evidence` choke point now used
by both Career Twin scoring and JD/job matching, resume history +
reactivation endpoints, and a frontend resume-history UI with an
active/superseded badge. Full detail, root cause, and both automated and
live-browser proof (JD coverage swinging 67%→11%→67% across upload/
reactivate) is in the defect ledger's DEFECT-001 entry — not
duplicated here.

**Quality gate this pass**: backend 167/167 (was 165) passed, ruff clean,
mypy clean (153 files); frontend 70/70 (was 68) passed, `tsc`/`eslint`
clean, `next build` succeeds (25 routes, unchanged route count); Docker
backend+frontend rebuilt, migration ran clean against real non-empty
Postgres (single head `a3f1c9e6b2d4`), all 5 services healthy.

**Exact next unfinished action**: per the rescue plan's priority order,
the next item is #2 (re-confirm GraphRAG live with a fresh walkthrough —
low effort, likely already PASS) or #3 (assessment-domain breadth —
large effort, start with 2-3 new domains rather than all ~19 at once).
Do not start a new phase without first reading the defect ledger's
existing entry for it, since several areas turned out to be already
fixed or not applicable once actually investigated (see DEFECT-002+ in
the ledger for GraphRAG, job deduplication, and others).

## Premium visual transformation pass (2026-08-05, prior pass)

Continues the visual redesign from where the first pass (global design
system, shared UI primitives, Landing, Competition Entry, Career OS
Dashboard, Career Twin, Competition Mode) left off. This pass redesigns
every remaining major competition-visible screen with the same premium
design language (`bg-mesh` hero headers, `card-premium`/`card-glow-brand`
surfaces, the `text-h1`/`text-metric` type scale, the `animate-fade-up`/
`animate-scale-in`/`animate-draw-line` motion set already defined in
`app/globals.css`), builds a real GraphRAG root-cause page that did not
exist before, and fixes one genuine production bug found during
live-browser verification.

**1. New: `/graphrag` — the cinematic root-cause reveal.** The backend has
always had a real Neo4j-backed root-cause endpoint
(`GET /graph/root-cause/{question_id}`, `app/api/graphrag.py`) and a
frontend type (`GraphPathStepOut`) scaffolded for it, but no page or hook
ever called it — the "GraphRAG root-cause experience" the product spec
describes did not exist as a screen. Built this pass: `hooks/
use-graphrag.ts` (root-cause + concept-neighborhood + graph-health
queries), `hooks/use-resources.ts`, new types in `types/api.ts`
(`RootCauseResultOut`, `GraphSnapshotOut`, etc.), and `app/graphrag/
page.tsx` — a sequential-reveal node chain (student → missed question →
weak concept, root-cause-spotlighted → concept dependency → target-role
requirement → recommended resource) with distinct icon/color per node
type, a stored-fact-vs-model-inference badge on every step, a Neo4j/
relational-fallback badge, a confidence indicator, a collapsible
Technical View showing the raw path, and loading/empty/error states. The
missing-context warning and `is_inference` flag are read directly from
the backend response, not fabricated. Wired in from two places: a new
"See root cause" link on an incorrect assessment answer
(`app/assessment/page.tsx`, previously gave no feedback on right/wrong at
all — a real UX gap fixed as part of this wiring) and a "GraphRAG" entry
in the main nav. **Live-verified end-to-end**: answered a SQL assessment
question incorrectly in the running Docker stack, clicked "See root
cause," and confirmed the real Neo4j-backed chain rendered (concept
`Relational Model`, both target-role requirements, the linked resource
"The Relational Model in 10 Minutes") — not a mock.

**2. Redesigned with the premium system**: Interview Arena (`/interview`,
`/interview/[sessionId]` — six-mode selection grid, a real Web-Audio-API
amplitude visualizer added to `hooks/use-audio-recorder.ts` (was silent
before), a live recording timer, and a CARE-processing state during
evaluation), Interview Replay (synced timeline with click-to-seek markers,
a new communication-metrics panel surfacing data the API already returned
but the old page never rendered, an explicit "this is one answer, not
permanent Twin mastery" banner), Experiment Lab (slider + numeric hour
controls, confidence-range display derived from the existing
confidence/uncertainty fields, assumptions/evidence drawers, ranked
scenario comparison with a "Top recommendation" badge), Research Lab
(general-audience/technical-judge toggle, a raw-JSON export button, the
existing ablation tables gated behind the technical view), Trust Center
(a new CARE execution timeline visualizing route selection → agents → 
result for the selected decision, plus `?execution=` deep-link support so
links from Interview Replay/missions actually preselect the right
execution — they didn't before), Responsible AI Center (fixed a real
content bug: the page rendered `non_claims` under the "Never evaluates"
heading and never showed `does_not_evaluate` at all, even though the
backend has always returned both as distinct lists; now both render
correctly, plus a new "What CareerPilot will never do" section and a
consent-settings display that wasn't shown before), and all four role
dashboards (admin/faculty/placement/recruiter — distinct accent colors
per role, honest "cohort of one" warnings when `total_students <= 1`
rather than presenting single-student aggregates as a trend).

**3. Competition Mode integration**: the GraphRAG slide now shows a
schematic node-chain motif matching the new `/graphrag` page's visual
language (was badges only), and every data-backed slide (GraphRAG, CARE,
Interview, Experiment Lab, Research Lab, Responsible AI) gained an
"Open the live [X]" link so a presenter can drop out of the fullscreen
deck into the real interactive screen for Q&A.

**4. One real production bug found and fixed via live-browser
verification, not code review alone**: the root layout's no-flash
theme-detection inline script (`app/layout.tsx`) imported
`THEME_STORAGE_KEY` from `lib/theme-provider.tsx`, a `"use client"`
module, and interpolated it into a `dangerouslySetInnerHTML` template
literal. Next's RSC boundary serializes client-module exports referenced
from a Server Component as client references — so instead of the literal
string `"careerpilot_theme"`, the built script embedded the stringified
body of Next's "cannot call a client function from the server" error
shim, which itself contains an unescaped apostrophe (`"It's not
possible..."`) that broke out of the single-quoted string literal,
throwing `SyntaxError: missing ) after argument list` on **every single
page load** in the production Docker build (confirmed via
`read_console_messages`, not just inferred). Fixed by moving the constant
to a new plain module with no `"use client"` directive
(`lib/theme-constants.ts`), imported directly by both the server-rendered
layout and the client theme provider. Re-verified after a full
`docker compose up -d --build frontend`: `curl`'d the served HTML and
confirmed the real key `careerpilot_theme` now appears in the inline
script; re-navigated in a live browser tab and confirmed zero console
exceptions.

**Verified live, this pass** (against the rebuilt Docker stack, logged in
as the demo student): GraphRAG empty state → assessment incorrect-answer
flow → live root-cause chain reveal; Interview Arena mode selection →
session → typed-answer submission → CARE-processing state → evaluation
reveal; Trust Center execution timeline for the resulting interview
evaluation; Research Lab "Run Experiment A" (real reliability-bin data
updated, run history entry appeared, export button present); Experiment
Lab "Run scenario" (current-vs-simulated reveal, confidence range,
delta bars); Responsible AI Center evaluates/does-not-evaluate split;
a role dashboard's 403 access-restricted state (demo account has no
faculty/admin role); Competition Mode opening slide and the GraphRAG
slide's new chain motif and live-reveal link.

**Regression gate, all re-run after every change in this pass**: the
redesign's first pass through `role-dashboards.test.tsx` caught two real
regressions in the new copy — a faculty-dashboard student-count string
that no longer matched the pluralization the test asserts, and a
recruiter-dashboard disclaimer that had accidentally started containing
the word "probability" (a pre-existing test correctly asserts that word
must never appear on that page, since the constitution forbids ever
implying a hiring probability). Both fixed in the app copy, not by
loosening the tests. Final state: frontend 68 tests / 17 files passing;
`tsc --noEmit` clean; `eslint .` clean across the whole frontend; `next
build` succeeds, 25 routes (up from 24 — the new `/graphrag` route);
`docker compose up -d --build frontend` — all 5 services healthy.

**What's honestly not done this pass**: formal screenshot capture across
every route × light/dark × three resolutions (only 2 new real screenshots
were captured — `/graphrag` empty and populated states — added to the
existing 9 under `docs/presentation/screenshots/`; the other newly
redesigned screens were verified live in-browser but not saved as image
files); no dedicated axe-core re-run against the newly redesigned screens
(the prior pass's accessibility fixes to shared primitives — `Progress`
aria-labels, `CardTitle` heading levels, `ErrorState` `titleAs` — were
reused as-is in every new page, but the new bespoke markup, e.g. the
GraphRAG node chain and the Interview Arena audio visualizer, was not
independently re-audited); no physical projector test; light theme was
spot-checked visually only (screenshot above is dark theme, the app
default). No backend code was touched this pass — this is entirely a
frontend redesign plus the one theme-script bug fix.

## Final technical closure pass (2026-08-05, prior pass)

Closes the two documented verification gaps from the prior adversarial
audit pass (below): a real accessibility audit (was manual-spot-check-only)
and a real dependency vulnerability scan (was "not run in this
environment"). No new product features; no scoring/research changes.

**1. Accessibility audit — axe-core 4.12.1, live against the real Docker
stack** (not a static lint rule): injected into a real logged-in browser
session via a local static file server serving the installed `axe-core`
npm package, run against every competition-critical route plus the
broader route set (23 of 24 routes; `/onboarding` and `/register` not
reached since they require an unauthenticated/fresh-account flow).

Found and fixed, all live-reverified to 0 violations after each fix:
- **Serious**: `aria-progressbar-name` — the shared `Progress` bar
  component (used ~15 call sites: dashboard skill bars, Career Twin
  components, interview dimension scores, job-match coverage, faculty/
  placement/recruiter aggregates) had no accessible name. Added a
  descriptive `aria-label` at every call site.
- **Serious**: `color-contrast` — the destructive button variant (`bg-
  danger text-white`) paired dark theme's light-red `--danger` token
  (#f87171, tuned for *text* on dark backgrounds) with white text,
  landing at ~2.8:1 contrast against WCAG AA's 4.5:1 minimum. Fixed with a
  theme-invariant `bg-red-600` for that one variant, leaving `--danger`'s
  other (correct) uses untouched.
- **Moderate, systemic**: `heading-order` — the shared `CardTitle`
  component always rendered `<h3>`, but on nearly every page a `Card` is
  the first content directly after the page's `<h1>` with no `<h2>`
  between them (13 files: trust-center, interview, interview replay,
  experiment-lab, research-lab, responsible-ai, assessment, resume,
  job-description, settings, admin, faculty, placement, recruiter). Added
  an `as="h2"|"h3"|"h4"` prop to `CardTitle` (default unchanged) and
  applied `h2` at every first-level Card usage.
- **Moderate**: `page-has-heading-one` — `ErrorState`'s title was always a
  `<p>`, so any page whose data-fetch fails (or, for the four role
  dashboards, whose viewer lacks the role) rendered with zero headings.
  Classified every call site by whether `ErrorState` is genuinely the
  page's only content (9 sites: dashboard, career-twin, interview session,
  interview replay, responsible-ai, admin, faculty, placement, recruiter —
  now `titleAs="h1"`) vs. nested inside a page that already has its own
  h1 (5 sites: assessment, job-description, resume, settings, trust-center
  — left as `<p>` to avoid a duplicate h1).
- **Moderate**: `region` — Competition Mode's fullscreen presentation
  overlay had no landmark regions at all (a real, if lower-priority,
  finding for a kiosk-style UI). Converted its header/content/footer
  `<div>`s to `<header>`/`<main>`/`<footer>`, visually identical.
- One flagged `color-contrast` on the landing page (`/`) was investigated
  and is a **verified axe false positive**, not fixed: `getComputedStyle`
  on the exact flagged elements (`Log in`, `Explore the demo` links)
  returns `rgb(243,242,251)` text on a transparent background (~17:1
  real contrast against the page's near-black background), confirmed
  against a screenshot showing clearly legible white text. Documented
  rather than "fixed" with a change that would have done nothing.
- 12 new/updated backend files were not touched by this section — this is
  entirely a frontend pass (24 files changed).

Real gaps not closed this pass, stated honestly:
- Viewport resize testing (tablet/mobile breakpoints) could not be
  mechanically driven in this environment — the browser automation tool's
  window-resize call did not change the page's actual CSS viewport
  (`window.innerWidth` stayed at 1707px after requesting 400px), a tooling
  limitation confirmed by direct measurement, not a skipped step. The
  codebase does use responsive Tailwind breakpoints (`sm:`/`md:` classes)
  throughout, verifiable from source, but this was not visually
  spot-checked at real mobile/tablet widths this pass.
- No screen-reader (NVDA/JAWS/VoiceOver) session was run — axe-core checks
  the accessibility tree mechanically; it is not a substitute for a human
  screen-reader pass. **MANUAL ACTION REQUIRED.**
- No physical projector test. **MANUAL ACTION REQUIRED.**
- Light theme was not swept with axe (dark is the app default and what
  every check above ran against).

**2. Dependency vulnerability scan — `pip-audit` + `npm audit`, real
run**: backend had one vulnerable package (`setuptools` 65.5.0, a
build-tool transitive dependency, 4 CVEs, none reachable through this
app's own code paths) — fixed by pinning `setuptools>=78.1.1` in
`backend/Dockerfile`'s install step, verified inside the rebuilt image.
Frontend: 0 vulnerabilities across 621 dependencies. Full detail in
`docs/security/SECURITY_REVIEW.md` "Dependency vulnerability scan."

**3. Regression validation, all re-run after the above**: backend 165
tests / ruff / mypy all clean (unchanged counts — this pass touched no
backend test-covered logic); frontend 68 tests / tsc / eslint / `next
build` (24 routes) all clean; full clean `docker compose down -v && build
--no-cache && up -d` from empty volumes — 5/5 services healthy, single
migration head `074b58839c25`, demo reset verified (real interview +
4 experiment scenarios + 5 research/ablation runs on first boot), and
Competition Mode/Research Lab/Interview Replay/Experiment Lab all
re-verified live in a real browser against the rebuilt production images
(not the dev server used for the accessibility fix-iterate loop).

**4. Release freeze**: see `git log` for the closing commit and the
`careerpilot-competition-final` tag. Working tree clean; no secrets
tracked (`.env*` gitignored, only `.env.example` placeholders committed);
9 real screenshots captured this pass under `docs/presentation/
screenshots/` (fictional seeded demo account only, no real person's
data); demo resume/audio fixtures were already fictional/synthetic
(confirmed: "Aanya Sharma" is a fabricated persona from `app/seed/
seed_demo.py`, the audio fixture is a generated silent WAV, not a real
recording).

See `docs/implementation/FINAL_ACCEPTANCE_MATRIX.md` for the updated
item-by-item status.

## Independent adversarial audit pass (2026-08-05, prior pass this session)

Closes the two genuine gaps the prior "Final Beast Master" pass disclosed
honestly (below, unchanged) — demo dataset completeness and the ablation
harness — plus one real bug found and fixed along the way. Everything
below is independently re-verified in this pass, not assumed from the
prior pass's claims.

**What changed:**

1. **Demo dataset completeness** (`app/seed/seed_demo.py`): the seeded
   demo account now has a real completed Interview Arena session (4
   questions, mixed mode, one answer via a real audio fixture, real
   resume-claim evidence verification, real Interview Replay timeline
   markers, real Career Twin impact), 4 real Experiment Lab scenarios
   (SQL, Data Structures, Communication, a balanced 30h mix), and a full
   run of the Research Lab suite (all 6 ablations) — all through the same
   service layer the live screens call, not hand-crafted rows. Competition
   Mode steps 9-11 (previously honest empty states) now show real data.
   The Neo4j graph seed also now runs automatically on every container
   boot (was a manual `docker compose exec` step) — "restart the backend
   container" is now a genuine one-click demo reset with zero manual
   commands.
2. **All six ablation seams** (`app/evaluation/ablations.py`, new): seams
   1-3 (CARE, graph retrieval, vector retrieval) reuse the existing
   Experiment A/B code with explicit ablation labels; seams 4-6 (Career
   Twin memory, reflection, consensus) are a new harness that calls the
   real `MemoryAgent`/`CriticAgent`/`ConsensusAgent` over curated case
   sets and reports real before/after deltas — including one honest
   negative finding (`MemoryOutput.confidence` is currently a constant,
   not graded — disclosed, not hidden). New API endpoint `POST
   /research/experiments/ablations`, new Research Lab UI card, 12 new
   backend tests (`test_ablations.py`). See `docs/research/ABLATION_GUIDE.md`.
3. **Real bug found and fixed**: seven cross-table foreign keys (e.g.
   `interview_sessions.target_role_id`, `experiment_results.baseline_
   snapshot_id`) had no `ON DELETE` behavior. Once the demo account had
   real interview/experiment/Career-Twin history (from fix #1 above), the
   very next backend restart's reseed crashed with a Postgres
   `ForeignKeyViolation` deleting the old demo account — a real,
   reproducible bug this same pass's changes exposed, caught by actually
   restarting the container rather than assuming it would work. Fixed
   with `ON DELETE SET NULL` on all seven (migration `074b58839c25`,
   Postgres-only — SQLite test connections don't enforce FKs in this
   project so the migration is a guarded no-op there). Live-verified with
   three consecutive backend restarts against real Postgres from a fresh
   volume, each recovering in ~10 seconds (target was <15s).
4. **One real UI bug found and fixed**: the four role-gated dashboards
   (admin/faculty/placement/recruiter) rendered a generic red "Something
   went wrong" / "Try again" error card for what is actually a correct
   403 authorization boundary — alarming and misleading (retrying repeats
   the same denial forever). `components/ui/error-state.tsx` now renders
   a calm "Access restricted" state with a link back to the dashboard
   when the error is a 403, found via live adversarial browser testing of
   unauthorized access (not a code read).

**Verified live, this pass:**

- Clean `docker compose down -v && build --no-cache && up -d` from empty
  volumes: migrations run clean, graph seed runs automatically, demo seed
  runs automatically, all 5 services healthy, `/health/dependencies`
  returns `ok` with all three dependencies `true`.
- Restart persistence for a throwaway non-demo account across `docker
  compose restart backend postgres neo4j` (created via the real
  `/auth/register` API, deleted afterward via the real Responsible AI
  account-deletion endpoint).
- Neo4j outage, Redis outage, and **Postgres outage** (not previously
  tested live) — `/health` and `/health/dependencies` stayed responsive
  and honestly reported `degraded` in all three cases; full recovery
  confirmed after restarting each service.
- Cross-user IDOR, role-based 403s, rate limiting, CORS, and Responsible
  AI export/deletion isolation — see `docs/security/SECURITY_REVIEW.md`
  "Independent re-verification pass."
- Full browser walkthrough of every major route (dashboard, Career Twin,
  resume, job match, assessment, Interview Arena + Replay, Experiment
  Lab, Research Lab, Trust Center, Responsible AI, settings, all four
  role-gated dashboards, Competition Mode all 14 steps) as the demo
  student — no broken links, no raw JSON exposure, no empty major stage.
- Quality gate re-run after every change (see below) — 165 backend tests
  (up from 159), 68 frontend tests (unchanged — no new frontend test
  file was warranted for a two-branch UI fix already covered by existing
  role-dashboard tests), ruff/mypy/tsc/eslint all clean, `next build`
  succeeds (24 routes, unchanged).

**What's still honestly not done** (unchanged from the prior pass, not
newly discovered): no recorded video, printed poster, or physical stage
rehearsal (require a human and physical hardware); a dedicated axe-core
accessibility audit across all 24 routes wasn't run (manual spot-checks
only); dependency vulnerability scanning (`pip-audit`/`npm audit`)
wasn't run. See `docs/implementation/FINAL_ACCEPTANCE_MATRIX.md` for the
full item-by-item status.

## "Final Beast Master" pass (prior pass, unchanged below)

Last verified: 2026-08-05. **"Final Beast Master" pass complete.** Every
milestone independently tested and Docker-verified: **P0 (Interview
Arena)**, **Career Twin `twin-v2` safeguard**, **P1 (Experiment Lab +
Simulation Engine)**, **Responsible AI Center**, **Research Benchmark Lab**
(routing comparison + graph-vs-vector + calibration), a **security review
pass** (3 real medium-severity fixes: audio upload size/type validation,
Redis-backed auth rate limiting), **minimal role dashboards** (faculty/
placement/recruiter/admin), **Competition Mode** (live end-to-end 14-step
smoke test passed), a **premium UI pass** (1 real bug found and fixed:
toast notifications blocking the header theme-toggle button), a
**production engineering pass** (consolidated `/health/dependencies`
endpoint; confirmed request-ID middleware and structured logging were
already in place from Phase 2; live-verified degraded/recovered status
against the real Docker stack), and **final acceptance testing**
(`FINAL_ACCEPTANCE_MATRIX.md`, `FINAL_RELEASE_COMPLETION_REPORT.md`). See
`FINAL_BEAST_MASTER_EXECUTION_PLAN.md` for the full sequencing and honest
scoping statement; `PHASE_3_EXECUTION_PLAN.md` for the P0/P1 narrative;
`FINAL_ACCEPTANCE_MATRIX.md` for the item-by-item status of every area the
original release scope named. Phase 2's original validation remains below,
unchanged and still green.

## What's left, stated honestly

**(Superseded by the adversarial audit pass above.)** The two pre-demo
housekeeping steps this section used to list (run one real Interview
Arena session and one real Experiment Lab scenario before presenting) are
done automatically now — the demo seed does this on every container
boot, no manual pre-demo action required. See "Independent adversarial
audit pass" at the top of this file. Everything else in
`FINAL_ACCEPTANCE_MATRIX.md`'s "Known gaps" section is future-work, not a
defect.

## Latest quality gate (2026-08-05, after the adversarial audit pass)

```
backend:  pytest -q                         -> 165 passed
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (152 files)
          alembic heads                     -> single head 074b58839c25
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 68 passed (17 files)
          next build                        -> succeeds (24 routes)
```

## Prior quality gate (after the production engineering pass, superseded above)

```
backend:  pytest -q                         -> 159 passed
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (151 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 68 passed (17 files)
          next build                        -> succeeds (24 routes)
docker:   backend rebuilt this pass; all 5 services healthy;
          live-verified GET /api/v1/health/dependencies: "ok" with all 3
          dependencies true, then stopped neo4j+redis and confirmed
          "degraded" with database still true (base /health stayed 200
          throughout), then restarted both and confirmed recovery back
          to "ok"
git:      11 commits this pass (e1f8bf5 P0+P1, efb2c28 Responsible AI,
          654ea12 Research Lab, e238b16 Security review, 7943578 role
          dashboards, 356b6bc Competition Mode, 1765743 presentation/
          research docs, 8c7aac7 toast/theme-toggle fix, 6a94ea4
          dependency-health endpoint, c73c998 production-engineering
          checkpoint, plus this pass's final acceptance-matrix/completion-
          report commit) -- all on `main`

Live e2e smoke test (this pass): logged into Docker frontend as
demo.student@careerpilot.ai, walked all 14 Competition Mode steps via
keyboard nav, confirmed evidence-backed numbers matched the dashboard,
confirmed honest empty states on steps with no stored data (not
fabricated), confirmed Escape exits cleanly to /dashboard.
```

## Exact next unfinished task

None outstanding from the Final Beast Master scope. See
`FINAL_RELEASE_COMPLETION_REPORT.md` §6 for optional future work
(pre-demo data seeding for Competition Mode steps 9-11, automated
ablation harness, dedicated accessibility audit).

## Status: Phase 3 P0 + P1 complete

### Career Experiment Lab + Simulation Engine (P1)

Deterministic, versioned (`sim-v1`) what-if simulation over hour
allocations (skill + activity type + hours, mixed allocations supported),
grounded in the student's real Career Twin, evidence diversity, concept
dependencies, their own job description's requirements, and their own
historical Career Twin trend — never an LLM-computed number.
`ExperimentExplainerAgent` may restate the numbers in prose but has no path
to alter them. New: `backend/app/simulation/engine.py`,
`backend/app/services/experiment_service.py`, `backend/app/agents/
experiment_explainer_agent.py`, `backend/app/api/experiments.py`,
`backend/app/schemas/experiment.py`, `backend/app/models/experiment.py`,
migration `957a79bda179`, frontend `/experiment-lab`. Full formula in
`docs/implementation/EXPERIMENT_LAB_SIMULATION.md`.

Verified live: ran "20h SQL", "20h DSA", and "20h Communication" scenarios
against a real student's Career Twin through the Docker stack, then
compared all three side by side (assumptions, evidence-used counts, and
the mandatory disclaimer all correct on every card).

### Quality gate for this checkpoint (cumulative)

```
backend:  pytest -q                         -> 133 passed (117 P0-checkpoint baseline + 16 new P1 tests)
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (139 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 53 passed (50 P0-checkpoint baseline + 3 new P1 tests)
          next build                        -> succeeds (19 routes, incl. /experiment-lab)
docker:   backend + frontend images rebuilt; all 5 services healthy;
          migration head 957a79bda179
```

### Interview Arena (P0)

Full voice/typed mock-interview loop: session start (6 modes) → question →
recording-or-typed answer → CARE-routed multi-agent evaluation → Interview
Replay → Trust Center trace → Career Twin evidence. Real route diversity
(confirmed live, not just asserted): a strong, on-topic technical answer
settles on `single_agent`; a thin/off-topic/ungrounded answer is honestly
flagged `evidence_conflict=True` and escalates toward `multi_agent`/
`critic_reflection`.

New: `backend/app/models/interview.py`, `backend/app/services/
{interview_service,speech_to_text}.py`, 5 new agents (`communication_agent`,
`technical_agent`, `hr_agent`, `resume_evidence_agent`, `jd_alignment_agent`),
`backend/app/api/interviews.py`, `backend/app/schemas/interview.py`,
migration `ccca34eecf1f`, frontend `/interview`, `/interview/[sessionId]`,
`/interview/[sessionId]/replay`.

### Career Twin small-sample safeguard (`twin-v2`)

A scoring-integrity review after the first live Interview Arena walkthrough
found that a single two-question session had produced a Career Twin
snapshot reading "Technical 90%, Communication 100%" — technically paired
with low confidence (28%/37%), but not visibly guarded against, and with no
distinction between "evidence repeated from one source" and "evidence from
independent sources." Fixed with three deterministic, versioned levers in
`backend/app/career_twin/scoring.py` (formula bumped `twin-v1` →
`twin-v2`): evidence-diversity weighting, prior-weighted (Bayesian
shrinkage) scoring that pulls the *stored score itself* toward a neutral
0.5 prior when evidence is sparse/narrow (not just confidence), and a hard
confidence cap (0.50) plus explicit `is_low_sample`/`low_sample_notice`
fields below the stability thresholds (3+ evidence items, 2+ distinct
source types). Verified live: the same test account's next interview
session produced version 2 with Technical shrunk 90%→60% (confidence
14%), Communication 100%→75% (confidence 28%), both displaying "Strong
performance in this session, but more evidence is required to establish
long-term proficiency." Full rule in
`docs/implementation/CAREER_TWIN_SCORING.md` "Small-sample safeguard";
tests in `backend/tests/test_career_twin_small_sample_safeguard.py` (one
strong answer, several strong answers from one source, conflicting
evidence, repeated evidence from one source, evidence from multiple
independent sources — all 6 passing). Migration `7ba5f89c3126`.

### Quality gate for this checkpoint

```
backend:  pytest -q                         -> 117 passed (111 interview-arena baseline + 6 new safeguard tests)
          ruff check app tests              -> clean
          mypy app --ignore-missing-imports -> clean (132 files)
frontend: tsc --noEmit / eslint             -> clean
          vitest run                        -> 50 passed (48 interview-arena baseline + 2 new safeguard-label tests)
          next build                        -> succeeds (18 routes, incl. 2 new dynamic interview routes)
docker:   backend + frontend images rebuilt; all 5 services healthy;
          migration head 7ba5f89c3126; both the Interview Arena flow and
          the twin-v2 safeguard verified live in a real browser against
          this stack (not just automated tests)
```

## Status: Phase 2 fully accepted (re-verified)

All 20 Phase 2 acceptance criteria pass. Phase 1's 20 acceptance criteria
remain green (28/28 original tests still pass, unmodified).

### This validation pass specifically proved

- **All 6 CARE routes** exercised through the real persisting
  `run_care_task()` engine (not just the pure routing function) —
  `tests/test_care_engine_routes.py`, 8/8 passing.
- **GraphRAG real-Neo4j → fallback → recovery**, live: stopped Neo4j
  mid-session, confirmed no crash, confirmed the relational fallback
  returns an identical path labeled `graph_source: "relational_fallback"`,
  restarted Neo4j, confirmed it resumed using the real graph. The Trust
  Center now surfaces this label in the UI (`AgentRunOut.output_payload`
  was previously omitted from the API response).
- **The full student journey through the actual frontend browser**:
  dashboard → root cause → Trust Center → 13-question adaptive assessment
  (including a free-form AI-graded question) → Career Twin v4→v5 → change
  explanation, all clicked through by hand, not scripted against the API.
- **Restart persistence** for a real (non-demo) student's assessment
  attempt, evidence, mission, Twin history, `CareExecution`, and
  `AgentRun` rows across `docker compose restart backend postgres neo4j`
  — every ID and value matched exactly before and after. (The seeded demo
  account is unsuitable for this proof: it resets by design on every
  backend restart — see the note below.)
- **Cross-student authorization isolation**, live and now a permanent
  suite: `tests/test_authorization_isolation.py`, 7/7 passing.
- **Frontend test coverage for every new Phase 2 screen**: 16 → 40 tests.

## What's running right now

```
docker compose ps
```

| Service  | Image                    | Port(s)            | State           |
|----------|--------------------------|---------------------|-----------------|
| postgres | pgvector/pgvector:pg16   | 5432                | healthy         |
| redis    | redis:7-alpine           | 6379                | healthy         |
| neo4j    | neo4j:5-community        | 7474, 7687          | healthy — seeded (16 concepts, 14 deps, 20 questions, 14 resources, 55 skills, 2 job roles) |
| backend  | careerpilot-ai-backend   | 8000                | running         |
| frontend | careerpilot-ai-frontend  | 3000                | running         |

Started via `docker compose up --build -d`. Graph seeded via
`docker compose exec backend python -m app.graphrag.run_seed` (idempotent,
safe to re-run any time — every write is a Cypher `MERGE`).

## URLs

- Frontend: http://localhost:3000 (`/dashboard`, `/assessment`,
  `/trust-center`, `/career-twin`, `/resume`, `/job-description`,
  `/settings`)
- Backend health: http://localhost:8000/api/v1/health
- Graph health: http://localhost:8000/api/v1/graph/health
- API docs: http://localhost:8000/docs

## Demo credentials

```
Email:    demo.student@careerpilot.ai
Password: DemoPass!2026
```
Seeded student now has a real weak-SQL-JOIN evidence point, producing a live
"Close the gap: Inner Join" mission with a real GraphRAG-derived root cause
the moment the seed script runs — no manual setup needed.

## Migration state

```
docker compose exec backend alembic current
# -> 298c98dafbbb (head)
```

Four migrations total: `788d1325f003` (Phase 1 schema), `2e021960668e`
(roles/skills seed), `2d1305695e6c` (Phase 2 schema — assessment/resource/
care/retrieval/evaluation tables), `298c98dafbbb` (assessment taxonomy +
resource catalog seed).

## Bug found and fixed in this checkpoint

**Postgres-only migration failure**: `2d1305695e6c` added `NOT NULL` JSON
columns (`tasks`, `resource_ids`, `outcome_evidence_ids`) to the existing
`learning_missions` table without a `server_default`. SQLite's lenient
`ALTER TABLE` hid this in local testing (empty table every time, fresh
per-test DB); real Postgres rejected it against a table that already had
rows (`column "tasks" ... contains null values`) — caught only once this
migration ran against the persistent, non-empty Postgres volume in Docker.
Fixed with `server_default='[]'` on all three columns; re-verified with a
full container rebuild against the same non-empty database (the failed
migration rolled back transactionally, so no manual cleanup was needed).

## Second bug found and fixed: Trust Center silently omitted `graph_source`

`AgentRunOut` (the API schema for a CARE agent run) didn't include the
`output_payload` column, even though the ORM model always stored it — so
the GraphRAG agent's `graph_source` field ("neo4j" vs.
"relational_fallback") was captured in the database but never reached the
API response or the Trust Center UI. Found while proving the Neo4j
fail/recover cycle end-to-end (§18.3 of the completion report). Fixed by
adding `output_payload: dict` to `AgentRunOut` and a "Neo4j graph" /
"Relational fallback (Neo4j unavailable)" badge to `/trust-center`;
covered by `test_trust_center_labels_relational_fallback_when_neo4j_query_fails`.

## Quality gate (all green as of this checkpoint)

```
backend:  pytest -q         -> 89 passed (73 prior + 8 CARE-route + 7 auth-isolation + 1 fallback-label)
          ruff check app    -> clean
          mypy app          -> 0 errors / 122 files
frontend: tsc --noEmit      -> clean
          eslint            -> clean
          vitest run        -> 40 passed (16 prior + 24 new Phase 2 screen tests)
          next build        -> succeeds (13 static routes)
docker:   all 5 services healthy; restart-persistence and Neo4j
          fail/recover cycle verified live (see completion report §18)
```

## Files changed in this checkpoint (Phase 2, on top of the Phase 1 checkpoint)

New: `backend/app/ai/**`, `backend/app/care_engine/**`, `backend/app/agents/**`,
`backend/app/graphrag/**` (seed/repository/service/schemas, was an empty
Phase 0 scaffold), `backend/app/evaluation/**`, `backend/app/services/
{retrieval_service,assessment_service,resource_service,autonomous_loop_service,
trust_center_service}.py`, `backend/app/models/{assessment,resource,care,
retrieval,evaluation}.py`, `backend/app/api/{assessments,resources,
trust_center,graphrag}.py`, `backend/app/schemas/{assessment,resource,
trust_center}.py`, `backend/alembic/versions/{2d1305695e6c,298c98dafbbb}*.py`,
`backend/app/seed/assessment_taxonomy.py`, frontend `/assessment` and
`/trust-center` pages, `hooks/use-{assessment,trust-center}.ts`,
`components/dashboard/care-activity-card.tsx`.

Modified: `backend/app/career_twin/scoring.py` (assessment component wired
in, trend/uncertainty helper), `backend/app/services/mission_service.py`
(root-cause enrichment), `backend/app/services/{resume_service,
job_description_service}.py` (retrieval indexing hooks), `backend/app/models/
{skill,mission}.py` (new columns), `backend/pyproject.toml` (+neo4j,
+anthropic), frontend `types/api.ts`, `mission-card.tsx`, `nav-links.ts`,
`dashboard/page.tsx`.

## Files changed in the final acceptance validation pass (on top of the above)

New: `backend/tests/test_care_engine_routes.py` (8 tests, all 6 CARE
routes through the real persisting engine), `backend/tests/
test_authorization_isolation.py` (7 tests, cross-student IDOR coverage),
frontend `__tests__/{assessment-page,trust-center-page,mission-card,
twin-timeline,care-activity-card}.test.tsx` (24 tests total).

Modified: `backend/app/schemas/trust_center.py` (`AgentRunOut` gained
`output_payload`), `backend/tests/test_trust_center_api.py` (added the
Neo4j-fallback-labeling test), frontend `types/api.ts` (`AgentRunOut.
output_payload`), `app/trust-center/page.tsx` (graph-source badge).

## Next time you pick this up

- The Docker stack may still be running from this session — check
  `docker compose ps` before starting a fresh one.
- If you restart the `backend` container, `demo.student@careerpilot.ai`
  resets to its known-good seeded state (by design — see "Files changed"
  above and completion report §15). Any other account's data persists
  normally across restarts.
- See `PHASE_2_COMPLETION_REPORT.md` §19 for the Phase 3 prerequisite list.
