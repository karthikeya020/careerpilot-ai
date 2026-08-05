# Final Slide Content — 12 Slides

Slides support the live demo; they do not duplicate it. No slide repeats
an app screen — every slide either sets up a moment the demo is about to
show, or lands a claim the demo just proved. Design direction: dark
background matching the app's own dark theme (`#0b0a12` background,
`#8b7bff` brand accent), the same gradient-orb motif from Competition
Mode's opening slide as the recurring visual anchor, large type (readable
from the back of a lecture hall — see `PROJECTOR_CHECKLIST.md`), minimal
text per slide (a judge should never be reading a paragraph while you
talk).

This supersedes `SLIDE_CONTENT.md` (13 slides, more screen-by-screen) as
the leaner, presentation-day deck; that file remains as a longer reference
if a venue wants more detail slides for a poster session or a printed
leave-behind.

---

## Slide 1 — Opening problem

**One-line message**: Career tools give you a score. None of them show
their work.

**Minimal visible text**:
> Disconnected tools. No memory. No explanation. No evidence.

**Visual**: Three faded, crossed-out generic-tool icons (resume grader,
chatbot bubble, static quiz checkmark) fading into darkness, no logos.

**Speaker notes**: Land this in under 10 seconds — this is the hook, not
the pitch. "Every one of you has used a career tool that gives you a
score with no explanation." Do not over-explain; the discomfort is the
point.

**Transition into live demo**: none yet — Slide 2 follows immediately,
then cut to Tab A `/competition` for the live hook.

---

## Slide 2 — CareerPilot solution

**One-line message**: An AI system that remembers, explains, and never
invents.

**Minimal visible text**:
> CareerPilot AI — The Career Operating System

**Visual**: The gradient orb from Competition Mode's opening slide,
centered, subtle pulse animation if your slide tool supports it.

**Speaker notes**: "CareerPilot AI is the Career Operating System that
shows its work — every number traced to real evidence, every
recommendation explained, nothing invented." This is your one-sentence
elevator pitch; judges who remember nothing else should remember this
line.

**Transition into live demo**: cut directly to Tab A, `/competition`,
step 1 — begin the live seven-minute script here.

---

## Slide 3 — Career Twin

**One-line message**: One persistent, evidence-backed model — confidence
included, never hidden.

**Minimal visible text**:
> 6 components. Every score paired with its confidence and evidence count.

**Visual**: A stylized version of the six-component radar chart (same
shape as `/dashboard`'s "Skill readiness overview"), one axis dimmed and
labeled "insufficient evidence" to show the honesty mechanism at a
glance.

**Speaker notes**: Use this slide *after* the live Career Twin demo, as a
recap before moving on, not before — the brief's guidance is "avoid long
technical explanations before demonstrating the product." One line:
"Never a fabricated number. `insufficient_evidence` when there isn't
one."

**Transition into live demo**: return to Tab A for the GraphRAG root-cause
reveal (step 4→5).

---

## Slide 4 — CARE architecture

**One-line message**: Six routes. Chosen per-decision, not fixed.

**Minimal visible text**:
> single agent → multi-agent → critic reflection → human review
> (+ deterministic, + graph-augmented)

**Visual**: A simple horizontal decision flow — evidence sufficiency and
confidence as inputs, six labeled boxes as outputs, one lit up (single
agent) to match what the live demo just showed.

**Speaker notes**: "CARE decided one specialist was enough here because
evidence was strong — when it isn't, CARE escalates. You'll see the proof
of that adaptivity in the research numbers in a minute" — this line
deliberately sets up the payoff in the Research Proof segment.

**Transition into live demo**: none needed if shown right after the live
CARE Decision step; otherwise cut to Tab A step 6.

---

## Slide 5 — GraphRAG root-cause reasoning

**One-line message**: A root cause is a graph traversal, not a guess.

**Minimal visible text**:
> student → failed question → concept → missing prerequisite → role requirement

**Visual**: The exact chain as a simple left-to-right node diagram (5–6
nodes, arrows between them) — this is the single highest-value visual in
the whole deck; give it its own slide with nothing else competing for
attention.

**Speaker notes**: Show this **after** the live GraphRAG reveal as a
recap of the chain the audience just heard narrated — pair the visual
with the verbal chain so people who process visually and people who
process verbally both land on the same understanding.

**Transition into live demo**: cut to Tab A step 6 (CARE Decision).

---

## Slide 6 — Connected student transformation

**One-line message**: One student, one continuous story — not six
disconnected features.

**Minimal visible text**:
> Evidence → Twin → Root cause → Mission → Interview → Twin update

**Visual**: A simple looping arrow diagram, six labeled stops, closing
back on "Twin" to show the loop is continuous, not linear.

**Speaker notes**: This is the slide that answers "why does this need to
be one product instead of six separate tools" — say that sentence
explicitly. "Every stop on this loop is real data from the same student
account, not six demos stitched together."

**Transition into live demo**: cut to Tab B, Interview Replay (already
covered the mission step live; this slide bridges into showing the
interview evaluation).

---

## Slide 7 — Experiment Lab

**One-line message**: What-if planning, computed by a formula — never an
LLM guessing.

**Minimal visible text**:
> "Personalized scenario estimate — not a guaranteed outcome or hiring
> prediction."

**Visual**: A simple before/after bar (73% → 75.5%) with the disclaimer
text large underneath — the disclaimer *is* the visual message, not fine
print.

**Speaker notes**: "No LLM invents this number — a versioned, deterministic
formula does. Diminishing returns, evidence diversity, historical trend,
role requirements." Keep this under 10 seconds; the live "Run scenario"
click is the actual proof, this slide is just the label.

**Transition into live demo**: cut to Tab B, Experiment Lab, click "Run
scenario" live.

---

## Slide 8 — Research evidence

**One-line message**: We measured it. We show the numbers that don't
flatter us too.

**Minimal visible text**:
> CARE adaptive: 100% · Fixed baseline: 12.5%
> Graph traversal: 100% · Vector-only: 50%

**Visual**: Two simple side-by-side bar pairs, high contrast, large
numerals — this is a "read from the back row" slide, minimal decoration.

**Speaker notes**: "Six real ablations, run against the real production
agents. One of them found a real limitation in our memory agent, and we
disclosed it instead of hiding it — that's what an honest ablation study
looks like." This last sentence pre-empts the "why is one result
negative" judge question before it's asked.

**Transition into live demo**: cut to Tab B, Research Lab, click "Run all
6 ablations" live.

---

## Slide 9 — Responsible AI

**One-line message**: What this system will never do, on the record.

**Minimal visible text**:
> No hiring probability. No lie detection. No public ranking. No inferred
> emotional state.

**Visual**: Four short lines, each with a red "✕" — deliberately mirrors
the actual `/responsible-ai` page's "Never evaluates" panel styling, so a
judge who saw the live screen recognizes it instantly.

**Speaker notes**: Say all four lines aloud, don't just point at the
slide — this is the ethics credibility moment, it needs your voice, not
just text on a screen.

**Transition into live demo**: cut to Tab A step 12 (Responsible AI) if
not already shown live before this slide.

---

## Slide 10 — Institutional / business value

**One-line message**: One evidence model, three audiences, zero
surveillance.

**Minimal visible text**:
> Faculty: cohort gaps. Placement: program effectiveness. Recruiters:
> opt-in only.

**Visual**: Three small labeled icons (mortarboard, chart, briefcase) in
a row, each with its one-line value prop beneath — no dashboard
screenshots (the live demo, or the honest cohort-of-1 caveat, already
covers that).

**Speaker notes**: Land the recruiter line with emphasis: "opt-in only,
never a default-visible pool, and structurally incapable of an automated
hiring call — that's a liability and fairness feature, not a limitation."

**Transition into live demo**: none required — this slide can stand alone
during the institutional-scale beat, or pair with Tab A step 13.

---

## Slide 11 — Architecture and reliability

**One-line message**: Built to survive an outage, not just a demo.

**Minimal visible text**:
> FastAPI · PostgreSQL · Neo4j · Redis · Docker Compose
> 165 backend tests · 68 frontend tests · offline-capable by default

**Visual**: A simple 5-box service diagram (backend, Postgres, Neo4j,
Redis, frontend) with one box (Neo4j) shown "unplugged" with a dotted
fallback arrow to Postgres — visually mirrors the live-tested
Neo4j-outage-and-recovery story.

**Speaker notes**: "Every one of these numbers is from a real command we
ran, not a slide claim — clean Docker rebuild from empty volumes, all
five services healthy, verified this week." Keep it to one sentence;
save depth for a technical judge's follow-up question.

**Transition into live demo**: none — this is a credibility slide for
Q&A, not a demo cue. Good slide to leave on screen during open Q&A.

---

## Slide 12 — Final vision

**One-line message**: Past. Present. Simulated future.

**Minimal visible text**:
> CareerPilot AI
> Your Career. Continuously Evolving.

**Visual**: The gradient orb again (bookends the deck with Slide 2),
slightly larger/brighter — a deliberate visual callback signaling "we've
come full circle."

**Speaker notes**: Deliver the closing line from `FINAL_STAGE_SCRIPT.md`
verbatim, then stop talking — let the slide sit in silence for a beat
before opening the floor to questions.

**Transition into live demo**: none — this is the final slide. If you
exited Competition Mode with `Esc` during the live closing, this slide
covers the moment while the room applauds/transitions to Q&A.
