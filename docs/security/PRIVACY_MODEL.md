# Privacy Model

## What is collected

| Data | Source | Where stored |
|---|---|---|
| Email, hashed password | Registration | `users` (Postgres) |
| Full name, target role, career goals | Onboarding | `student_profiles`, `target_roles`, `career_goals` |
| Resume file + parsed text/sections/skills | Resume upload | File on disk (`var/uploads/<student_id>/`) + `resumes`/`resume_sections`/`resume_skills` (Postgres) |
| Job description text | JD paste/upload | `job_descriptions` (Postgres) |
| Assessment answers and scores | Adaptive assessment | `assessment_attempts`/`question_responses` (Postgres) |
| Interview audio (when recorded) | Interview Arena | File on disk (`var/uploads/<student_id>/interview_audio/`) |
| Interview transcript | Interview Arena (live STT, deterministic demo transcript, or typed) | `interview_answers.transcript` (Postgres) |
| Career Twin snapshots, evidence, missions, CARE decision traces, audit events | Continuous product use | Postgres, immutable/append-only by design |
| Experiment Lab scenarios | Career Experiment Lab | `experiment_scenarios`/`experiment_results` (Postgres) |

**Never collected**: biometric data, facial imagery, location, device
fingerprinting beyond the request IP (used only transiently for rate
limiting, never persisted).

## Consent

- `StudentProfile.consent_settings` records explicit onboarding consent
  (`data_processing`). Surfaced back to the student in the Responsible AI
  Center overview.
- Recording an interview answer is an explicit student action (clicking
  "Record answer" triggers a real browser microphone-permission prompt);
  declining or the browser lacking `MediaRecorder` support always leaves
  the typed-answer path fully usable (Prompt 3: never block on mic
  denial). No audio is captured without that per-recording browser-level
  permission grant.

## Student-controlled data rights (implemented, not just documented)

All under `/responsible-ai`, backed by `app/services/responsible_ai_service.py`:

| Right | Endpoint | Behavior |
|---|---|---|
| **Export** | `GET /responsible-ai/export` | Full JSON export of profile, resumes, job descriptions, skill evidence, Career Twin snapshots, missions, assessment attempts, interview sessions, experiment scenarios, and audit events -- everything stored about the student, in one document. |
| **Withdraw audio consent** | `DELETE /responsible-ai/interview-audio` | Deletes every stored audio file for the student and clears the file-path pointer. **Transcripts and evaluations are kept** -- this is audio-specific consent withdrawal, not full erasure, and the UI states that distinction explicitly. |
| **Full deletion ("right to be forgotten")** | `DELETE /responsible-ai/account` (password-confirmed) | Deletes the `User` row; every child row (student profile, resumes, evidence, Career Twin history, missions, assessments, interviews, experiment scenarios, audit events) cascades via `ondelete=CASCADE` foreign keys. Uploaded files on disk are removed from the student's upload directory. Login with the deleted account's credentials afterward returns `401`. |

## Data minimization

- Interview evaluation agents receive only the specific transcript and
  question being evaluated -- not the student's full history -- except
  `MemoryAgent`, which is invoked deliberately (only on the `multi_agent`
  council path) and reads recent missions/evidence *counts and titles*,
  never raw transcript content from other sessions.
- The Research Lab's Experiment B indexes only concept *descriptions*
  (shared domain knowledge, `student_profile_id=NULL`) into the vector
  store -- never student-specific text.
- Role dashboards (faculty/placement) are aggregate-only by default; no
  per-student drilldown is exposed without an explicit, separately
  authorized route (see `docs/implementation/FINAL_BEAST_MASTER_EXECUTION_PLAN.md`
  Milestone D).

## Retention

- No automatic time-based deletion is implemented in this pass -- data
  persists until the student exercises the deletion controls above. This
  is disclosed as a limitation: a production deployment should add a
  configurable retention policy (e.g., delete audio N days after an
  interview, per an institution's data-retention agreement).
- The seeded demo account (`demo.student@careerpilot.ai`) is deliberately
  reset on every backend container restart (Phase 2 `CURRENT_CHECKPOINT.md`)
  -- this is a demo-reliability feature, not a privacy control, and does
  not apply to real student accounts.

## Third parties

- No AI provider call happens unless `PRIMARY_LLM_API_KEY` /
  `SPEECH_TO_TEXT_API_KEY` is explicitly configured. In that configuration,
  the relevant request content (e.g., an interview transcript sent to a
  live speech-to-text or chat provider) leaves the process and is subject
  to that provider's own data-handling terms -- this should be disclosed to
  users in any deployment that enables a live provider, and is called out
  here so it is not silently assumed.
