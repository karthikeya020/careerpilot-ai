# Presentation Day Runbook

The single master document for the day itself. Everything else in
`docs/presentation/` is referenced from here — if you only print one
document to bring on stage, print this one plus the sticky-note summary
at the bottom.

## Document map

| Document | Use it for |
|---|---|
| `FINAL_STAGE_SCRIPT.md` | The word-for-word 7-minute script — your primary reference |
| `THREE_MINUTE_DEMO.md` | Emergency cut if your slot is shortened |
| `TWELVE_MINUTE_DEMO.md` | Extended cut for a judge-interview / deep-dive slot |
| `FINAL_SLIDE_CONTENT.md` | 12-slide deck content, if the venue wants slides |
| `FINAL_POSTER_CONTENT.md` | Poster/booth content |
| `BACKUP_VIDEO_STORYBOARD.md` | Recording plan if you produce a backup video before the event |
| `JUDGE_Q_AND_A.md` | 16 core questions, 15s/30s/deep answers each |
| `PROJECTOR_CHECKLIST.md` | Hardware, software, and venue-readiness checklist |
| `REHEARSAL_SCORECARD.md` | Track rehearsal quality across 5 attempts before the event |
| `BACKUP_DEMO_PLAN.md` | What happens if a specific dependency fails live (Neo4j, Redis, mic, etc.) |
| `SCREENSHOT_CHECKLIST.md` | Which static fallback screenshots exist and which are still needed |

---

## Timeline of the day

**T-minus 24 hours**
- Final rehearsal (rehearsal 5 on the scorecard) — full run, timed, with
  an audience if at all possible.
- `docker compose down -v && docker compose build --no-cache && docker
  compose up -d` — one full clean rebuild, confirm all 5 services
  healthy, confirm demo login works.
- Confirm the backup laptop has the same clean build.
- Charge everything.

**T-minus 2 hours**
- Arrive at the venue if a tech-check window exists. Run the
  `PROJECTOR_CHECKLIST.md` "Visual readability (verify in venue)" section
  for real, in the real room.
- Test the actual HDMI/adapter chain you'll use, not a different port.

**T-minus 30 minutes**
- `docker compose restart backend` — final reset.
- Run `PROJECTOR_CHECKLIST.md` "Immediately before you go on" in full.
- One quiet read-through of the opening 30 seconds out loud, once, to
  yourself.

**T-minus 5 minutes**
- Both tabs open, logged in, fullscreen.
- Phone silent and out of sight.
- Stop rehearsing — trust the prep.

**On stage**
- Follow `FINAL_STAGE_SCRIPT.md`. If time is cut, see its "If you're
  running long or short" section before improvising.

**Immediately after**
- Do not reset the demo account until Q&A is fully over — judges may ask
  you to click back into something you already showed.
- After Q&A: `docker compose restart backend` to return to a clean state
  for the next presenter/slot if the venue is running back-to-back demos
  on shared hardware.

---

## Known rough edges (say these out loud if asked — don't get caught by
## a judge finding them first)

- **No in-app "past interviews" list.** Reaching a specific interview's
  Replay page requires knowing its session ID — there's no navigable
  history view yet. The two-tab setup in `FINAL_STAGE_SCRIPT.md` works
  around this by pre-loading the URL before you go on stage. If a judge
  asks you to "pull up a different interview," be honest: "that specific
  navigation isn't built yet — here's the one I have loaded, and here's
  the API that proves the data exists for every session," and show
  Trust Center's execution list instead.
- **Institutional dashboards show a cohort of one.** The seeded demo
  database has exactly one real student account. Faculty/placement/
  recruiter/admin dashboards are real and tested but will show
  aggregate-of-one, not a populated cohort, unless you've pre-registered
  additional throwaway accounts before the event (normal use of
  `/register` + `/onboarding` — no code change needed, just time). If you
  want a fuller institutional-scale visual for a 12-minute slot, do this
  the day before, not live.
- **CARE routing in the seeded interview stays "single agent."** All four
  seeded interview answers were strong enough that CARE never escalated
  to a multi-agent council in this specific demo account. The adaptivity
  claim is real and measured (see the Research Lab's 100% vs. 12.5%/25%
  routing-agreement numbers) but isn't demonstrated by *this* specific
  live click — the script deliberately bridges from "single agent, chosen
  because evidence was sufficient" to "here's the proof it escalates when
  it isn't," landing in the Research Proof section rather than promising
  something the live click won't show.
- **Numbers drift a few points between resets.** The seed re-runs real
  agent code on every `docker compose restart backend`, not a fixed
  script — an interview answer's confidence might read 63% one run and
  61% the next. Read the number on screen; don't force-fit a memorized
  figure if it's drifted slightly.
- **Mobile/tablet layouts were not visually verified** in the most recent
  audit pass (a browser-automation tooling limitation, not a skipped
  step — see `docs/implementation/CURRENT_CHECKPOINT.md`). Don't demo on
  a phone or a resized window unless you've separately confirmed it looks
  right.

---

## If something breaks live

**General rule**: every empty state, error state, and degraded-mode
message in this product was built to be honest, not to hide a crash. If
something looks "off," read what's actually on screen before assuming
it's broken — it may be the product correctly telling you it's degraded.

| Symptom | What's actually happening | What to do |
|---|---|---|
| A screen shows "Access restricted" | You're logged in as the wrong role for that dashboard | Expected for the demo student on `/admin`, `/faculty`, `/placement`, `/recruiter` — narrate over it per `TWELVE_MINUTE_DEMO.md`'s "role dashboards" row, don't panic-click |
| A Competition Mode step shows an empty message | Extremely unlikely after the demo-seed pipeline, but if it happens, the underlying data genuinely isn't there | Press `→` to move to the next step and keep narrating; mention it's an honest empty state, not a crash, if a judge notices |
| Neo4j-dependent screen shows a "relational fallback" label instead of "Neo4j" | Neo4j is down or still starting | This is the *feature* working as designed — say so explicitly, it's a stronger moment than if nothing had happened |
| Browser tab frozen / unresponsive | Rare Chrome/CDP hiccup, not an app bug | Alt+Tab away and back once; if still frozen, switch to the backup laptop rather than fighting it on stage |
| Whole stack unreachable (`docker compose ps` shows unhealthy) | Full rebuild needed (~2 minutes) — too slow to fix live | Switch immediately to the backup laptop (already running a clean build) rather than debugging in front of the audience |
| Backup laptop also fails | Genuine worst case | Play the backup video if one was recorded (`BACKUP_VIDEO_STORYBOARD.md`); if not, present from the screenshot deck (`docs/presentation/screenshots/`) and `PROJECT_PITCH.md`/`TECHNICAL_DIFFERENTIATORS.md` narration — all real, honest artifacts that carry a Q&A without a live system |

**Recovery target**: under 15 seconds for any single-service hiccup
(Neo4j/Redis/backend restart) — this was live-verified during the
technical audit pass, not just claimed. A full rebuild is the only
failure mode that genuinely costs real time, which is exactly why the
backup laptop exists as a parallel, always-ready fallback rather than
something you build during the failure.

---

## Escalation / who does what (fill in before the event)

- **Primary presenter**: _____________________
- **Backup presenter** (can take over mid-demo if primary has a technical
  issue and needs to troubleshoot): _____________________
- **Laptop/AV owner** (manages the hardware swap if the backup laptop is
  needed): _____________________
- **Timekeeper** (visible hand signal at 5:00, 6:00, 6:45 marks if
  possible): _____________________

---

## Sticky-note summary (literally write this on an index card)

```
RESET:     docker compose restart backend
KEYS:      → / Space next · ← previous · R reset · F fullscreen
           · T technical view · Esc exit
TAB B URL: [fill in after your final pre-show reset]
IF STUCK:  switch to backup laptop, don't debug on stage
TIMING:    0:30 Twin | 1:20 GraphRAG | 2:10 CARE | 2:50 Interview
           3:45 Experiment | 4:50 Research | 5:40 Responsible | 6:15 Close
```
