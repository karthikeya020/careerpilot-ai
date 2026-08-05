# Backup Video Package — Storyboard

**Status: this is a text storyboard and recording plan only. No video has
been recorded.** Recording, editing, and exporting all require a human at
a keyboard with screen-capture software — out of scope for an automated
pass. Do not present this document, or claim in front of judges, that a
finished video exists. See `PRESENTATION_DAY_RUNBOOK.md` "Manual actions
still required." This supersedes `VIDEO_SCRIPT.md` as the fuller
storyboard; that file remains as a shorter 3-minute-only draft.

The purpose of this package: if the live demo is genuinely impossible
(venue Wi-Fi blocks localhost somehow, laptop fails with no backup, room
has no HDMI), a **pre-recorded** fallback is the last resort *below* the
backup laptop and the screenshot deck in `PROJECTOR_CHECKLIST.md`'s
priority order. Record this before the event, not during it.

---

## Seven-minute storyboard

Shot list mirrors `FINAL_STAGE_SCRIPT.md` exactly — same clicks, same
narration, same timing. Record it by literally following that script with
screen capture running. Differences from the live version are called out
per shot below (mainly: no live Alt+Tab risk, cut on a clean edit
instead).

| # | Time | Shot | Screen | Narration (verbatim from FINAL_STAGE_SCRIPT.md) | On-screen caption |
|---|---|---|---|---|---|
| 1 | 0:00–0:30 | Opening slide, orb animation, static hold | `/competition` step 1 | "Every one of you has used a career tool..." (full hook) | *(none — let the visual breathe)* |
| 2 | 0:30–1:20 | Cut to step 2, then step 3 | `/competition` steps 2→3 | Career Twin Awakening narration | "73% overall · 36% confidence — shown honestly" |
| 3 | 1:20–2:10 | Cut to step 4, then step 5 | `/competition` steps 4→5 | GraphRAG chain narration | "Root cause: a real graph traversal, not a guess" |
| 4 | 2:10–2:50 | Cut to step 6, then step 7 | `/competition` steps 6→7 | CARE + mission narration | "CARE: 6 routes, chosen per-decision" |
| 5 | 2:50–3:45 | Cut to step 8→9, then a clean cut (not a live alt-tab) to the Interview Replay page | `/competition` step 8→9, then `/interview/[id]/replay` | Interview Replay narration, scroll to the technical question | "Real replay. Real per-dimension scoring." |
| 6 | 3:45–4:50 | Clean cut to Experiment Lab, pre-stage the click so "Run scenario" is caught mid-animation | `/experiment-lab` | Experiment Lab narration | "Deterministic formula — not an LLM guess" |
| 7 | 4:50–5:40 | Clean cut to Research Lab, "Run all 6 ablations" click caught live | `/research-lab` | Research proof narration | "CARE 100% vs. fixed baseline 12.5%" |
| 8 | 5:40–6:15 | Cut to step 12, then step 13 | `/competition` steps 12→13 | Responsible AI + institutional narration | "No hiring probability. No lie detection. No ranking." |
| 9 | 6:15–7:00 | Cut to step 14, hold on final frame | `/competition` step 14 | Closing narration | "Your Career. Continuously Evolving." |

## Three-minute storyboard

Shot list mirrors `THREE_MINUTE_DEMO.md`. Six shots, hard cuts between
each (no need to show the rapid `→` key presses on camera — cut straight
to the landed step):

| # | Time | Shot | Screen | Narration | Caption |
|---|---|---|---|---|---|
| 1 | 0:00–0:20 | Opening | step 1 | Hook | *(none)* |
| 2 | 0:20–0:50 | Career Twin | step 3 | Twin narration | "73% · 36% confidence" |
| 3 | 0:50–1:25 | GraphRAG | step 5 | Root-cause chain | "Graph retrieval used" |
| 4 | 1:25–2:05 | Experiment Lab | step 10 | Simulation narration | "Not a guaranteed outcome" |
| 5 | 2:05–2:40 | Research proof | step 11 | CARE/graph numbers | "100% vs. 12.5%" |
| 6 | 2:40–3:00 | Closing | step 14 | Closing line | "Your Career. Continuously Evolving." |

---

## Exact screen-recording sequence

1. **Before recording**: `docker compose restart backend` for a fresh,
   known-good state (see `FINAL_STAGE_SCRIPT.md` "Before you walk on
   stage" for the full reset + Tab B session-ID lookup). Close every
   other app, disable notifications, set display to 1920×1080.
2. Open the recording software, set capture region to the full browser
   window (fullscreen, `F` in Competition Mode).
3. Start recording **5 seconds before** the first click, so the edit has
   clean lead-in room. Do the same at the end — hold the final frame 5
   seconds after the last narration word.
4. Record video and a **separate scratch audio track** (even if narrating
   live over the recording) — this makes it possible to re-record just
   the narration later without re-capturing the screen.
5. Record each of the 9 (or 6, for the 3-minute cut) shots as **separate
   files** — easier to re-take one shot than the whole 7 minutes if a
   click misfires. Number the files `01_opening.mp4`, `02_twin.mp4`, etc.
   matching the shot-list table above.
6. For shot 5 (Interview Replay) and shots 6–7 (Experiment Lab, Research
   Lab): do the real click on camera (don't cut away before clicking
   "Run scenario" / "Run all 6 ablations") — the button-press-to-real-
   result moment is the actual proof point; cutting around it would
   undercut the "not staged" claim this whole video exists to back up.

## Narration

Use the verbatim spoken-word blocks from `FINAL_STAGE_SCRIPT.md` (7-minute
cut) or `THREE_MINUTE_DEMO.md` (3-minute cut). Options, in order of
preference:
1. **Live narration while recording** — most natural pacing, matches how
   you'll actually sound on stage (good rehearsal value too).
2. **Separate voiceover recorded after**, synced in editing — cleaner
   audio, easier to re-take a flubbed line without re-capturing video.
3. If neither: on-screen captions alone (see below) can carry the video
   with no narration, at a cost to impact — last resort only.

## On-screen captions

Burn in (not just YouTube-style auto-captions, which can mis-transcribe
technical terms like "GraphRAG" or "CARE") the short caption from each
storyboard row above, timed to appear ~1 second after narration starts
and clear ~1 second before the next cut. Keep captions to the short
phrase in the table, never the full spoken paragraph — captions
reinforce, they don't duplicate.

## Recording checklist

- [ ] Fresh demo reset immediately before recording (not hours before —
      numbers drift slightly between resets, see `FINAL_STAGE_SCRIPT.md`)
- [ ] Display set to 1920×1080, scaling 100%
- [ ] Browser fullscreen, bookmarks bar hidden, one clean tab per shot
- [ ] Notifications, Slack/email/OS popups disabled
- [ ] External mic if available (laptop mic picks up fan noise under
      Docker load)
- [ ] Each shot recorded as a separate file, 5s lead-in/lead-out padding
- [ ] A second full take of shots 5–7 (the live-click shots) in case the
      first take has any UI hitch
- [ ] Scratch audio track kept even if also narrating live

## Editing checklist

- [ ] Assemble shots in storyboard order, hard cuts (no crossfades — this
      is a product demo, not a montage)
- [ ] Trim each shot's lead-in/lead-out down to ~1s once narration is
      synced
- [ ] Burn in captions per the timing guidance above
- [ ] Add a title card (Slide 2 content from `FINAL_SLIDE_CONTENT.md`) as
      the opening 3 seconds, before shot 1
- [ ] Add a closing card (Slide 12 content) as the final 3 seconds, after
      the last shot
- [ ] Normalize audio levels across all shots (narration recorded across
      multiple takes will vary in volume)
- [ ] Full watch-through at 1x speed checking captions land on the
      correct word, not early/late
- [ ] Confirm final runtime is 6:50–7:05 (7-minute cut) or 2:55–3:05
      (3-minute cut) — pad or trim shot 1 or shot 9/6 (the bookend shots)
      to hit the window, never mid-demo shots

## Export settings

- Container: MP4 (H.264 video, AAC audio) — universally playable without
  a codec install on an unfamiliar venue laptop
- Resolution: 1920×1080, do not upscale from a lower capture resolution
- Frame rate: match the source capture (30fps is sufficient for UI
  screen-capture content; no need for 60fps)
- Bitrate: 8–12 Mbps video (UI text needs to stay sharp when projected;
  don't over-compress)
- Audio: 192kbps AAC, -16 LUFS target loudness (comfortable projector-
  speaker volume without clipping)
- Export a second copy at 720p / lower bitrate as a small-file fallback
  for a USB stick with limited space or a venue laptop with a slow disk

## Offline storage checklist

- [ ] Two USB drives, both with the final MP4 (both cuts: 7-minute and
      3-minute), labeled clearly
- [ ] One copy on the presentation laptop's local disk (not cloud-only —
      assume no venue internet)
- [ ] One copy on the backup laptop's local disk
- [ ] File names include the date and cut length, e.g.
      `careerpilot-backup-7min-2026-08-05.mp4`, so an old take is never
      confused with the current one
- [ ] Test playback on the actual presentation laptop (not just the
      editing machine) before the event — codec/driver mismatches are a
      real, common failure mode
- [ ] Test playback with the actual venue projector/adapter if a
      rehearsal slot in the room is available beforehand
