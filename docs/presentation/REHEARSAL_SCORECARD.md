# Rehearsal Scorecard

Score every full run-through (7-minute cut, start to finish, in front of
at least one other person if possible) across the 11 dimensions below,
1–5. Be honest — this document is only useful if the numbers are real.
Run at least 5 rehearsals before the actual event; more if any dimension
is still below 4 after rehearsal 5.

## Scoring guide (read once, apply consistently across all 5 attempts)

| Score | Meaning |
|---|---|
| 1 | Failed — did not land at all, or broke the flow |
| 2 | Weak — landed but unconvincing, needed real work |
| 3 | Adequate — got the point across, not memorable |
| 4 | Strong — clearly landed, minor polish left |
| 5 | Excellent — this is the version you want on the actual day |

## Dimensions

- **Opening impact** — did the first 30 seconds grab attention or did it
  feel like throat-clearing?
- **Clarity** — could a non-technical listener follow every section
  without getting lost?
- **Confidence** — did the presenter sound sure of the material, or was
  there hedging/filler?
- **Timing** — how close to the 7:00 target, and were individual section
  timings (see `FINAL_STAGE_SCRIPT.md`) roughly on track, not just the
  total?
- **Career Twin wow moment** (0:30–1:20) — did the 73%/36%-confidence
  honesty land as a deliberate feature, not a weakness?
- **GraphRAG wow moment** (1:20–2:10) — did the audience visibly follow
  the causal chain (question → concept → prerequisite → role), not just
  hear a wall of names?
- **Experiment Lab wow moment** (3:45–4:50) — did the live "Run scenario"
  click read as genuinely live, not pre-baked?
- **Technical credibility** — for the technical-judge asides: precise,
  confident, no hand-waving when pressed?
- **Audience comprehension** — after the run, ask your test audience to
  summarize the product in one sentence; score based on how close they
  land to "an AI system that shows its evidence and never invents a
  score"
- **Closing impact** — did the final line land, or did the energy fizzle
  before "thank you"?
- **Failure recovery** — deliberately trigger one hiccup per rehearsal
  (see "Inject one failure per rehearsal" below) and score how smoothly
  the presenter recovered without breaking narration flow

## Inject one failure per rehearsal

Rehearsals should not always go perfectly — the actual event won't.
Deliberately trigger one of these per attempt (rotate through them across
the 5 rehearsals) and score "Failure recovery" based on the response:

1. Kill the `neo4j` container mid-GraphRAG-section — does the presenter
   keep talking through the relational-fallback badge instead of
   panicking?
2. Have someone ask a hard judge question mid-flow (pull from
   `JUDGE_Q_AND_A.md`) — does the presenter answer and resume cleanly?
3. Close Tab B right before the Interview Replay switch — does the
   presenter recover by narrating Tab A's summary instead (see
   `FINAL_STAGE_SCRIPT.md` "If you're running long or short")?
4. Start the timer 90 seconds late (simulating a delayed slot) — does the
   presenter compress using the cut guidance in `FINAL_STAGE_SCRIPT.md`
   instead of rushing every section equally?
5. Full run with no injected failure — this is your clean baseline to
   compare recovery attempts against.

## Scorecard

| Dimension | Rehearsal 1 | Rehearsal 2 | Rehearsal 3 | Rehearsal 4 | Rehearsal 5 |
|---|---|---|---|---|---|
| Opening impact | | | | | |
| Clarity | | | | | |
| Confidence | | | | | |
| Timing | | | | | |
| Career Twin wow moment | | | | | |
| GraphRAG wow moment | | | | | |
| Experiment Lab wow moment | | | | | |
| Technical credibility | | | | | |
| Audience comprehension | | | | | |
| Closing impact | | | | | |
| Failure recovery | | | | | |
| **Total (/55)** | | | | | |
| **Actual runtime** | | | | | |
| **Injected failure (see above)** | | | | | |
| **One thing to fix before next rehearsal** | | | | | |

## After rehearsal 5

- If any single dimension is below 4 across all 5 attempts, that's your
  priority fix — don't spread remaining prep time evenly, concentrate on
  the weakest dimension.
- If total score is trending up but timing is still inconsistent
  (>±20s variance across attempts), do 2 more timing-only run-throughs
  with a visible stopwatch before the event, no audience needed.
- If "Failure recovery" never got above 3, add one more rehearsal with a
  harder injected failure than any of the five above (e.g., have someone
  physically unplug the HDMI cable mid-demo) — recovering from a genuinely
  startling hiccup is a different skill than reciting the recovery line
  calmly in a low-stakes rehearsal.
