# Screenshot Checklist

Static fallback assets to capture before presenting (see
`BACKUP_DEMO_PLAN.md` "absolute last resort"). Capture at 1920×1080 in
both light and dark theme where noted.

**Status as of the 2026-08-05 closure pass**: 9 of 26 items below are
real, captured image files, committed under `docs/presentation/
screenshots/` (all captured live against the real Docker stack, logged in
as the fictional seeded demo account `demo.student@careerpilot.ai` — no
real person's data). Captured at this browser automation tool's fixed
viewport (1512×795), not the 1920×1080 the venue may want for a
projector — re-capture at 1920×1080 before a live event if that matters.
The remaining 17 are genuinely not captured — **MANUAL ACTION REQUIRED**,
same as before this pass. Nothing here is claimed done that isn't.

- [x] `/competition` Opening slide — `screenshots/competition-opening.jpg`
- [x] `/dashboard` full view (Career Twin summary, mission, priority weakness, CARE activity card) — `screenshots/dashboard.jpg`
- [ ] `/career-twin` all six components visible, one showing `insufficient_evidence`
- [ ] `/career-twin` a component showing the `twin-v2` low-sample notice (light + dark)
- [x] `/trust-center` execution list — `screenshots/trust-center.jpg`
- [ ] `/trust-center` a `root_cause_analysis` execution detail, graph-source badge visible
- [ ] `/trust-center` a `multi_agent` or `critic_reflection` execution (route diversity proof)
- [ ] `/assessment` an adaptive question in progress
- [ ] `/interview` mode-selection screen
- [ ] `/interview/[id]` an in-progress question with recording controls + typed fallback both visible
- [ ] `/interview/[id]` an evaluation panel after submission (dimension scores, strengths/improvements)
- [x] `/interview/[id]/replay` full replay screen (transcript, timeline markers, evidence check) — `screenshots/interview-replay.jpg`
- [x] `/experiment-lab` scenario builder with allocations — `screenshots/experiment-lab.jpg` (shows the builder + 4 real seeded past scenarios; not the 3-way comparison view)
- [ ] `/experiment-lab` a result card (current vs. simulated, assumptions, disclaimer)
- [ ] `/experiment-lab` a 3-scenario comparison view
- [x] `/research-lab` — `screenshots/research-lab.jpg` (calibration + ablation run history; not specifically the Experiment A/B charts mid-run)
- [ ] `/research-lab` Experiment A result chart
- [ ] `/research-lab` Experiment B result chart with methodology note
- [ ] `/research-lab` calibration reliability bins (visible in the captured shot above, but not isolated as its own image)
- [x] `/responsible-ai` full page (evaluates/never-evaluates lists, versions) — `screenshots/responsible-ai.jpg`
- [ ] `/faculty` dashboard
- [ ] `/placement` dashboard
- [ ] `/recruiter` dashboard (with at least one opted-in candidate)
- [x] `/admin` dashboard — captured the **access-restricted state** (`screenshots/admin-access-restricted.jpg`), proof of this pass's 403-handling fix, not the service-health panel a real administrator account would see (no admin account exists in the seed data)
- [ ] `/settings` recruiter-visibility toggle
- [x] `/competition` Closing slide — `screenshots/competition-closing.jpg`
- [ ] Mobile-width screenshot of `/dashboard` (responsive layout proof) — **not captured this pass**: the browser automation tool's window resize did not change the actual CSS viewport in this environment (confirmed via `window.innerWidth` staying at 1707px after a resize call), a tooling limitation, not a skipped step. Needs a real device or a properly viewport-emulating tool.
- [ ] Light-theme and dark-theme side-by-side of any one screen (theme support proof) — every capture above is dark theme (the app's default); light theme was not captured this pass.

All 9 files above are real screenshots taken this pass against the live
Docker stack (`docker compose up`, demo account, no fabricated data) —
none are mockups or AI-generated images.
