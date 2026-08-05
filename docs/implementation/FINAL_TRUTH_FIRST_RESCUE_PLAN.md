# Final Truth-First Rescue Plan

## Why this document states scope honestly up front

The instruction driving this pass asks for a genuinely enormous scope:
a new active-resume data model, a rebuilt GraphRAG graph schema, a
~19-domain adaptive assessment engine with new question banks and a
no-repeat/spaced-review system, deep interview-audio NLP with an ethical
delivery-confidence framework, a job-provider/deduplication architecture,
a rebuilt Experiment Lab decision workflow, actionable Trust Center
evidence-correction tooling, actionable Responsible AI controls beyond
export/delete, a full second visual pass, projector/accessibility/
security validation across every route, and roughly a dozen new
documentation files — each phase individually described at a level of
depth (real question banks with misconceptions and prerequisites, real
NLP signal extraction, a real job-provider adapter layer) that represents
weeks of senior engineering and content-authoring work for a small team,
not hours for one session.

The instruction also explicitly anticipates this: it defines a "Context
and Continuation Protocol" for work spanning multiple sessions, and a
"Final Acceptance Rule" that forbids marking anything PASS that isn't
truly verified — PARTIAL must stay PARTIAL, BLOCKED must state its exact
reason, and manual physical work (a projector rehearsal, a recorded
video) cannot be claimed as done. Following that rule faithfully, rather
than fabricating breadth to match the prompt's scale, **is** the
truth-first execution the instruction asks for. Producing shallow stubs
across 15 phases to *look* complete would violate the instruction's own
explicit rules 4-13 more than doing one thing correctly and saying the
rest honestly wasn't reached.

## What this pass actually did

Investigated every reported problem area against the real, current
codebase (not the prior completion reports' claims — rule 5), reproduced
what was real, and repaired the single highest-severity, most-confirmed,
most-demoable defect found: **DEFECT-001, stale resume evidence**. See
`FINAL_TRUTH_FIRST_DEFECT_LEDGER.md` for full detail on every problem
area investigated, including the ones found to be already-fixed
(pre-existing, from the prior session), not-applicable (job
deduplication — no such feature exists to have this bug), or genuinely
out of reach this pass (a full multi-domain assessment curriculum).

DEFECT-001 was chosen first because it is:
- The user's own explicit priority #1 ("Resume replacement and
  stale-state repair").
- Real and severe: confirmed by reading `resume_service.py` and
  `career_twin/scoring.py` directly, not by assumption.
- The one defect that actively **contradicts the product's core promise**
  (an "evidence-grounded Career Twin" that silently uses evidence from a
  resume the student has since replaced is not evidence-grounded).
- Fully fixable and provably fixable within one session's scope, unlike
  a new assessment curriculum or a job-provider integration.

## Priority order for continuing this work

Following the instruction's own "Execution priority for tomorrow's
presentation" list, adjusted for what was found to already exist vs.
what is genuinely still open:

1. **Resume replacement and stale-state repair** — DONE this pass (DEFECT-001).
2. **Dedicated real GraphRAG experience** — already real from the prior
   session; re-confirm with a fresh live walkthrough rather than rebuild.
3. **Assessment domain breadth + no-repeat behavior** — genuinely open,
   largest remaining scope item. Recommend starting with 2-3 additional
   *real, carefully authored* domains (e.g. Data Structures, OOP) rather
   than all ~19 at once, plus the no-repeat/exposure-tracking mechanism,
   which is a smaller, well-scoped engineering task independent of
   content volume.
4. **Interview depth**: add pause/hesitation-duration signal extraction
   to the existing `CommunicationMetricsOut` pipeline, and add the
   explicit "observable delivery signals, not an emotional diagnosis"
   disclaimer text near any delivery-confidence display — this is a
   smaller, well-scoped task since the transcript/timing pipeline
   already exists.
5. **Job/company intelligence** — re-scope first: confirm with the
   product owner whether a real job-listing/marketplace feature is
   wanted (new feature) versus deepening the existing single-JD
   analysis (`/job-description`) with the 7-day/30-day plan and
   likely-assessment-domain suggestions Phase 6 also asks for, which
   *does* fit the existing feature and is achievable without a new
   provider-adapter architecture.
6. **Experiment Lab, Research Lab, Trust Center, Responsible AI** —
   visual/audience-clarity layer already real (prior session); the
   specific new actions (evidence correction/recompute, human-review
   request) are the open item, each independently schedulable.
7. Remaining route polish, full regression, presentation-safe reset —
   ongoing as each item above lands.

## What "done" looks like for this document going forward

Each future session should: read this file and the defect ledger first,
pick the next unstarted or partially-started item in the priority order
above, reproduce it against the live product before writing code (not
assume the ledger's prior description is still accurate), implement,
write a real automated test, verify live in a real browser against the
Docker stack, update the defect ledger entry's status honestly, update
`CURRENT_CHECKPOINT.md`, and commit — then stop and hand off rather than
continuing into a new item with degraded context.

## Documents intentionally not created this pass

The instruction names several additional documents
(`FINAL_TRUTH_FIRST_COMPLETION_REPORT.md`,
`FINAL_TRUTH_FIRST_ACCEPTANCE_MATRIX.md` — created, see below —,
`docs/design/FINAL_PRODUCT_ROUTE_AUDIT.md`,
`docs/design/FINAL_COMPETITION_UI_AUDIT.md`,
`docs/design/FINAL_SCREENSHOT_INDEX.md`,
`docs/research/FINAL_RESULTS_SUMMARY.md`,
`docs/presentation/FINAL_DEMO_ROUTE.md`,
`docs/presentation/FINAL_PRESENTATION_SAFE_CHECKLIST.md`). These were not
created this pass because they would either duplicate existing,
already-accurate documents from the prior session
(`docs/design/FINAL_VISUAL_TRANSFORMATION_REPORT.md`,
`docs/design/PROJECTOR_VISUAL_AUDIT.md`,
`docs/presentation/SCREENSHOT_CHECKLIST.md`) or would have no honest
content yet given this pass's narrow scope (a "completion report" and
"acceptance matrix" implying broad completion would misrepresent a
single-defect pass). `FINAL_TRUTH_FIRST_ACCEPTANCE_MATRIX.md` was created
because it is the one document that can honestly and usefully report
partial status without overclaiming.
