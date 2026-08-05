# Projector and Stage Checklist

Run through this the night before and again 30 minutes before your slot.
Items marked **(verify in venue)** need the actual room, not just your
desk — do them during any walkthrough/tech-check window the event offers.

## Hardware

- [ ] Presentation laptop, fully charged, charger packed
- [ ] **Backup laptop**, fully charged, charger packed, with the full
      Docker stack pre-pulled/pre-built (`docker compose build`) so it
      doesn't need internet on the day
- [ ] HDMI adapter for the presentation laptop (and a second, different
      adapter type if your laptop's port is uncommon — USB-C-only laptops
      should carry both HDMI and DisplayPort adapters)
- [ ] Second HDMI adapter for the backup laptop
- [ ] Wired mouse (trackpad gestures are harder to hit precisely on stage
      adrenaline)
- [ ] External mic or lapel mic if the venue doesn't provide one and the
      room is large
- [ ] Two USB drives with the backup video (`BACKUP_VIDEO_STORYBOARD.md`
      export, once actually recorded) and the screenshot deck
      (`docs/presentation/screenshots/`)
- [ ] Power strip / extension cable (venue outlets are often far from the
      podium)

## Software / stack

- [ ] `docker compose ps` — all 5 services healthy, checked within the
      last 30 minutes, not just "this morning"
- [ ] `docker compose restart backend` run for a **final** clean reset
      immediately before you're called up — see `FINAL_STAGE_SCRIPT.md`
      "Before you walk on stage" for the full sequence including the Tab
      B session-ID lookup
- [ ] Both browser tabs pre-opened and pre-logged-in (Tab A `/competition`,
      Tab B Interview Replay) — do this *after* the final reset, not
      before, since the reset recreates the demo account
- [ ] Browser set to fullscreen (`F` in Competition Mode, `F11` for the
      browser chrome itself if you want the URL bar hidden too)
- [ ] All OS/app notifications disabled (Do Not Disturb / Focus mode on)
- [ ] Bookmarks bar hidden, no other tabs open, no other apps running
      (Slack, email client, calendar popups all closed)
- [ ] Battery saver / screen-dimming / screensaver disabled for the
      duration
- [ ] Local Docker stack confirmed to need **zero internet** — put the
      laptop in airplane mode once and click through all 14 Competition
      Mode steps to prove it to yourself before the event

## Offline / backup readiness

- [ ] Offline demo path rehearsed at least once with Wi-Fi off (see
      above) — confirms no hidden network dependency snuck in
- [ ] Backup video exported and playback-tested **on the actual
      presentation laptop**, not just the editing machine (see
      `BACKUP_VIDEO_STORYBOARD.md` "Offline storage checklist")
- [ ] Screenshot deck (`docs/presentation/screenshots/`) available as a
      fallback if even the backup video can't play — 9 real screenshots
      exist as of this pass; see `SCREENSHOT_CHECKLIST.md` for exactly
      which ones and what's still missing
- [ ] USB copy of both the video and the screenshots on **two** separate
      drives (one is not a backup)
- [ ] One-click demo reset command written on a sticky note or index
      card taped to the laptop: `docker compose restart backend`
- [ ] Keyboard controls for Competition Mode written on the same card:
      `→`/`Space` next · `←` previous · `R` reset · `F` fullscreen ·
      `T` technical view · `Esc` exit

## Visual readability **(verify in venue)**

- [ ] Text visible from the **back of the room** — stand at the farthest
      seat during a tech check and read the smallest text on screen
      (calibration bin numbers and badge text are the smallest in the
      app; if those are legible, everything else is)
- [ ] Tested at both **100% and 125%** OS display zoom — pick whichever
      reads better on the venue's actual projector resolution and lock it
      in before you start
- [ ] Tested at both **1920×1080** and **1366×768** — some venues still
      run older projectors; know which one you're getting before you're
      on stage, not during
- [ ] Tested in the room's actual **dark classroom** lighting (lights off
      for the projector) — dark theme contrast checked
- [ ] Tested in the room's actual **bright/daylight** lighting if the
      event won't dim the room — this is the harder case; the app's dark
      theme can wash out under bright ambient light, so know in advance
      whether you need to request the lights dimmed
- [ ] Confirmed the projector doesn't crop or letterbox the browser
      content unexpectedly (aspect-ratio mismatches are a common surprise)

## Immediately before you go on

- [ ] Final `docker compose restart backend`, wait for confirmation
- [ ] Both tabs re-logged-in post-reset (the reset recreates the demo
      account's password but any stale session token should still work —
      re-login anyway to be certain)
- [ ] Fullscreen both tabs
- [ ] Phone on silent, out of sight
- [ ] Water within reach but off the podium/table the laptop sits on
- [ ] One full mental run-through of the first 30 seconds (the hook) —
      this is the part nerves hit hardest; the rest carries itself once
      you're moving
