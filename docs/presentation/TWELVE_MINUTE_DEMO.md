# Twelve-Minute Extended Demo

For a dedicated deep-dive slot (judge interviews, finalist round). Builds
on `SEVEN_MINUTE_DEMO.md` with the full student journey, Technical View
detail, role dashboards, research methodology, security, and business
value.

| Time | Segment | Screen |
|---|---|---|
| 0:00-0:30 | Opening | `/competition` step 1 |
| 0:30-1:30 | Full onboarding → resume → JD flow | `/onboarding`, `/resume`, `/job-description` (use a fresh or reset account to show the true empty→evidence transition) |
| 1:30-2:30 | Career Twin, Technical View | `/career-twin` + `/competition` step 3 with Technical View toggled on |
| 2:30-3:30 | GraphRAG root cause, graph badge | `/trust-center`, point out `graph_source` and the relational-fallback path (mention it was verified live by stopping Neo4j mid-session, Phase 2) |
| 3:30-4:00 | CARE routing table | Walk through the 6 routes conceptually, then show 2-3 real executions with different routes in Trust Center |
| 4:00-4:30 | Mission + autonomous loop | `/dashboard`, explain Observe→Diagnose→Plan→Teach→Assess→Reflect |
| 4:30-6:00 | Interview Arena full flow + Replay | `/interview` (pick a mode, record or type an answer) → evaluation → `/interview/[id]/replay` (audio, transcript, timeline, evidence check) |
| 6:00-7:00 | Experiment Lab, multiple scenarios | `/experiment-lab` — run 3 scenarios, compare all three, explain the `sim-v1` formula briefly (diminishing returns, evidence diversity, historical trend) |
| 7:00-8:00 | Research Lab, both experiments + calibration | `/research-lab` — run Experiment A and B live, show the calibration reliability bins |
| 8:00-8:45 | Role dashboards | `/faculty`, `/placement`, `/recruiter` (mention consent-gated visibility), `/admin` |
| 8:45-9:30 | Responsible AI + security posture | `/responsible-ai`; mention `docs/security/SECURITY_REVIEW.md` findings/fixes (audio upload validation, rate limiting) without reading the whole doc |
| 9:30-10:15 | Business value | Faculty/placement/recruiter value props from `BUSINESS_VALUE.md` |
| 10:15-11:30 | Judge Q&A buffer | Use `JUDGE_Q_AND_A.md` for likely questions |
| 11:30-12:00 | Closing | `/competition` final step |

If time runs short mid-demo, drop to the 7-minute skeleton by cutting the
role-dashboard and full-onboarding segments first — they're the least
essential to the core "wow" narrative.
