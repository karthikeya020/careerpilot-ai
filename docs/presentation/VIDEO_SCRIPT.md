# Video Script (Backup Demo Recording)

**Status: this is a text script only — no video has been recorded.**
Recording requires a human at a keyboard with screen-capture software,
which is out of scope for an automated coding session (see
`FINAL_BEAST_MASTER_EXECUTION_PLAN.md` §3 and
`FINAL_ACCEPTANCE_MATRIX.md` "Known gaps"). Do not present this as a
completed video asset — it is the shot list and narration a human
presenter would use to record one.

A ~3-minute screen-recording script to have as a pre-recorded fallback
(see `BACKUP_DEMO_PLAN.md` "absolute last resort"). Record at 1920×1080,
narrate live or dub afterward.

## Shot list

1. **(0:00-0:10)** `/competition` Opening slide, animated orb visible.
   Narration: "CareerPilot AI — the Career Operating System."

2. **(0:10-0:35)** `/career-twin` page, scroll through all six components.
   Narration: "Every score here comes from real evidence — resume,
   assessments, interviews. Never a fabricated number. This component
   shows insufficient evidence, honestly, not padded."

3. **(0:35-1:00)** `/trust-center`, open a `root_cause_analysis` execution,
   point at the graph-source badge.
   Narration: "When we find a weakness, we don't guess why — we trace it
   through a real knowledge graph."

4. **(1:00-1:40)** `/interview` — start an interview, submit a typed
   answer, show the evaluation panel with dimension scores.
   Narration: "CARE decides how much reasoning this answer needs — one
   specialist, or a full council — live, per answer."

5. **(1:40-1:55)** `/interview/[id]/replay` — scroll transcript and
   timeline markers.
   Narration: "Interview Replay shows exactly what happened, and why."

6. **(1:55-2:30)** `/experiment-lab` — run two scenarios, show the
   comparison, read the disclaimer aloud.
   Narration: "Students can simulate their next 20 hours before spending
   them — a deterministic formula, not an LLM guessing."

7. **(2:30-2:50)** `/research-lab` — run Experiment A live, show the chart
   appear.
   Narration: "And we can prove it — real experiments, run right now, not
   marketing numbers."

8. **(2:50-3:00)** `/competition` Closing slide.
   Narration: "CareerPilot AI. Your Career. Continuously Evolving."

## Technical notes

- Record with the deterministic provider active (no API key) so timing is
  consistent and reproducible on re-recording.
- Use the `demo.student@careerpilot.ai` account, freshly reset
  (`docker compose restart backend`) immediately before recording so the
  narrative state (weakness, mission, evidence) matches what's described
  in `docs/implementation/CURRENT_CHECKPOINT.md`.
- Caption file (if produced) should transcribe the narration verbatim for
  accessibility.
