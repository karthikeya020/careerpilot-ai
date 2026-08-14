# Technology Readiness Level Assessment

**Scale used:** the standard 9-level TRL scale (NASA/DoD origin, also used
by EU Horizon Europe and most innovation/incubation programs). This
document states our real, current TRL honestly, with evidence for every
claim, and a concrete engineering roadmap to the next levels — because an
inflated TRL claim collapses under a single follow-up question from a
technical judge, and a precise, evidenced one does not.

## Current level: **TRL 6** — system/subsystem prototype demonstrated in a relevant environment

TRL 6 requires a working prototype tested in an environment that
realistically represents the target use case — not a notebook demo, not a
slide deck, but a system a real user could actually operate. CareerPilot
AI clears this bar on evidence, not assertion:

| TRL 6 requirement | Evidence in this repo |
|---|---|
| Integrated system, not isolated components | FastAPI backend + Next.js frontend + Postgres + Neo4j + Redis, all wired end-to-end, deployed together via Docker Compose |
| Representative environment | Runs in containers against real Postgres/Neo4j/Redis, not mocks — the same shape of stack a small institutional deployment would use |
| Realistic operating conditions tested | Simulated outages: Neo4j and Redis stopped mid-run; confirmed `/health/dependencies` reports `degraded` and the app stays functional; confirmed recovery after restart |
| Core function validated end-to-end | A real resume, uploaded through the real parser, produces real stored `SkillEvidence` rows, which the scoring function (`career_twin/scoring.py`) turns into readiness components — traceable end-to-end, not spot-checked |
| Verification beyond "it runs" | 262 backend tests, 105 frontend tests, a real `axe-core` accessibility audit (found and fixed 5 classes of real issue), a real `pip-audit`/`npm audit` dependency scan (found and fixed a real CVE), an IDOR authorization-isolation test suite across every ID-addressable resource, a scoring-drift canary that has already caught and correctly forced a deliberate re-freeze on a real confidence-computation change |

This is meaningfully past TRL 5 (component validation in a relevant
environment) because the *whole system* — not a subsystem — has been
exercised under failure conditions and adversarial testing, and past a
naive TRL 6 because the verification depth (security review, accessibility
audit, resilience testing) is the kind of diligence normally associated
with pre-launch hardening, not a hackathon prototype.

## Why not TRL 7 yet — stated honestly

TRL 7 requires demonstration in an **operational** environment: real
users, making real decisions, with the system in situ over time. We are
explicitly not there, and no part of this codebase or its documentation
claims otherwise:

- The only "user" data is a single seeded demo account (`Aanya Sharma`),
  produced by running the real pipeline once against a real resume file —
  not hand-typed numbers — but still a demo fixture, not a live cohort.
- No multi-tenant institution isolation — one deployment, role-based
  within it, not yet built for concurrent institutional customers.
- No SSO/LMS integration (Canvas, Banner, etc.), which any real university
  deployment would require for account provisioning.
- No billing/subscription infrastructure.

These are the exact gaps `docs/presentation/BUSINESS_VALUE.md` already
lists under "what this prototype does not yet implement" — this
assessment isn't a new admission, it's the same honesty applied to a
formal TRL framework.

## Path to TRL 7, 8, 9 — the actual startup trajectory

This is the part that matters for demonstrating startup potential: the
gap between where we are and full operational deployment is a **known,
scoped, and mostly non-research engineering list** — not an open research
problem. That distinction is what makes this fundable/acceleratable
rather than a permanent prototype:

- **TRL 7** (operational pilot): onboard one real cohort (a university
  career-services office or bootcamp) for one term. Requires: SSO/LMS
  provisioning for that one institution, a real (non-seeded) onboarding
  flow at scale, and an incident-response runbook — no new AI research,
  all integration engineering.
- **TRL 8** (system complete and qualified): multi-tenant isolation,
  formal SLA/uptime monitoring, penetration testing by a third party (our
  own `docs/security/SECURITY_REVIEW.md` is a real internal review, not an
  external pen test), and a billing layer.
- **TRL 9** (proven in operational conditions): multiple paying
  institutional customers, retention/outcome data (do students who use
  this actually place better), and the operational history to prove the
  deterministic-fallback and resilience design holds up under real load,
  not simulated outages.

## One-paragraph summary (for the pitch)

> CareerPilot AI is at TRL 6: an integrated, end-to-end system —
> not a mockup — that has been security-reviewed, accessibility-audited,
> and resilience-tested against real simulated infrastructure failure,
> with 367 automated tests enforcing that every score a user sees traces
> back to real stored evidence. The path from here to a paying
> institutional pilot (TRL 7) is integration engineering we can already
> name — SSO, multi-tenancy, onboarding — not unsolved research, which is
> exactly the profile of a technology ready to accelerate as a startup
> rather than stay a permanent prototype.
