# CareerPilot AI — Project Constitution

CareerPilot AI is an evidence-grounded, confidence-aware, agentic Career
Operating System. These rules are permanent and apply to every phase of
development, by any contributor (human or AI). Code review and CI should
treat violations of these rules as blocking.

1. **Every readiness score must be derived from stored evidence.** No
   `ReadinessComponent`, `SkillState`, or Career Twin value may be written
   without at least one linked `SkillEvidence` / `Evidence` row, or an
   explicit `insufficient_evidence` status. Never fill a chart with an
   invented number.
2. **Every recommendation must reference its supporting evidence.** Missions,
   weaknesses, and matches must carry evidence IDs or an explanation a
   student/reviewer can trace back to a source artifact (resume, JD,
   assessment, evidence record).
3. **Every Career Twin update must create an audit record.** Writing a new
   `CareerTwinSnapshot` always writes a paired `DecisionTrace` and
   `AuditEvent` in the same transaction.
4. **AI-generated values must never be presented as factual certainty.**
   Surface confidence, evidence count, and formula/version alongside any
   derived score. Label estimates as estimates.
5. **No fake hiring prediction.** Never compute or display a "probability of
   being hired." Match/readiness output is coverage and alignment, not a
   hiring outcome.
6. **No public student ranking.** No leaderboard or cross-student comparison
   visible to students or unauthorized roles.
7. **No lie detection.** Never infer deception from resume, interview, or
   behavioral signals.
8. **No unsupported psychological or emotional inference.** Do not infer
   personality, emotional state, or mental health from any input.
9. **All AI providers must be replaceable through adapters.** Parsing,
   matching, and future LLM calls sit behind an interface
   (`app/services/*` adapter classes) so a provider swap never touches
   callers.
10. **All important AI outputs must use validated structured schemas.**
    Pydantic (backend) / Zod (frontend) schemas validate every AI-adjacent
    output before storage or render — no raw, unvalidated dict/JSON in the
    trust path.
11. **Database modifications require migrations.** Every model change ships
    with an Alembic migration. Never hand-edit the deployed schema.
12. **Tests must accompany major business logic.** Auth, RBAC, scoring,
    parsing, matching, and dashboard aggregation each require tests before
    being considered done.
13. **Demo-critical features require deterministic fallbacks.** If an
    external secret/service (LLM key, object storage, etc.) is absent,
    implement a clean local fallback rather than blocking the feature or the
    demo.
14. **Accessibility, mobile responsiveness, and error states are
    mandatory.** Every shipped page needs a loading state, an empty state,
    an error state, keyboard navigability, and a usable mobile layout.
15. **Secrets must never be committed.** Configuration comes from `.env`
    (git-ignored); `.env.example` documents keys with placeholder values
    only.
16. **Development must remain aligned with the project documents under
    `/docs`.** When code and docs disagree, reconcile explicitly — update
    the doc or change the code, don't let them silently diverge.
