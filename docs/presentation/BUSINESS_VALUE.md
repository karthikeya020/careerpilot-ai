# Business Value

## For students

- One system that remembers their evidence across resume, assessments,
  interviews, and learning activity — no re-explaining their background
  every session.
- A concrete, evidence-backed next action instead of generic advice.
- Interview practice that evaluates communication, correctness, and
  resume-claim consistency together, with a replay they can actually learn
  from (timeline markers, better-answer framework).
- A what-if planner (Experiment Lab) to make informed decisions about
  limited study time, with honest uncertainty instead of false precision.

## For universities / career-services departments (faculty & placement)

- Cohort-level skill-gap visibility without invasive per-student
  surveillance — aggregate-only by default, individual identification only
  where there's a legitimate need (students flagged for human-review
  outreach).
- A measurable signal for program effectiveness (average Career Twin
  delta across the cohort) instead of anecdotal feedback.
- Defensible, evidence-based reporting to institutional leadership: every
  number the dashboard shows traces back to real stored evidence, not a
  vendor's opaque "readiness score."

## For recruiters / employer partners

- Evidence summaries only for students who explicitly opt in — never a
  scraped or default-visible candidate pool.
- Confidence and human-review indicators alongside every evidence point,
  so a recruiter knows when to look closer rather than trust a number
  blindly.
- Explicitly no automated hiring recommendation — this is a liability and
  fairness feature, not a limitation: an institution deploying this tool
  is not exposed to algorithmic-hiring-discrimination risk because the
  system structurally cannot make that call.

## Why the architecture matters commercially

- **Provider-adapter design** (Constitution rule 11) means switching or
  adding an LLM provider — or running with none at all — never touches
  calling code. This directly lowers vendor lock-in risk and ongoing
  inference cost for an institutional buyer.
- **Deterministic fallback everywhere** means the product demos and
  functions reliably even during a provider outage — a real operational
  concern for any tool used during time-sensitive activities like a live
  mock-interview session.
- **Audit trail by construction** (every Career Twin change is paired with
  a `DecisionTrace` + `AuditEvent` in the same transaction) gives an
  institution a real answer to "how do we know this tool is being fair,"
  which increasingly matters for procurement in education technology.

## What this prototype does not yet implement

- Billing/subscription infrastructure.
- Multi-tenant institution isolation (currently single-deployment,
  role-based within one instance).
- SSO/LMS integration (Canvas, Banner, etc.) — a real deployment would
  need this for account provisioning.

These are explicitly out of scope for a competition prototype and don't
change the core technical differentiation described in
`TECHNICAL_DIFFERENTIATORS.md`.
