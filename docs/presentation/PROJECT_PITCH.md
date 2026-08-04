# Project Pitch — CareerPilot AI

## The problem

Career preparation today is a pile of disconnected tools: a resume
formatter, a generic "AI interview coach" chatbot, a static skills quiz,
maybe a spreadsheet of job applications. None of them remember the student
between sessions. None of them explain *why* a student is weak in a skill,
only that they got a question wrong. None of them tell a student what to
actually spend their next 20 hours on, with any grounded estimate of the
payoff. And every one of them is a black box — a score appears, with no
evidence, no confidence, no way to know if it's trustworthy.

## The solution

CareerPilot AI is an evidence-grounded, confidence-aware, agentic **Career
Operating System**. It builds one persistent **Career Twin** per student —
a living model of their readiness, built only from evidence it can point
to (a resume line, an assessment answer, an interview transcript, never an
invented number). When the Twin finds a weakness, **GraphRAG** traces it to
its actual root cause through a real concept-dependency graph, not a
guess. **CARE** (Confidence-Aware Reasoning Engine) decides — per
decision, live — whether a simple deterministic calculation, one
specialist agent, a full multi-agent council, or a critic/reflection pass
is warranted, and escalates to a human-review flag when confidence stays
low. The system then generates a targeted mission, evaluates the student's
spoken interview answers with the same evidence discipline, and lets the
student simulate *"what if I spent the next 20 hours on X instead of Y"*
with a deterministic, versioned formula — never an LLM inventing a
readiness gain.

## Career Twin

Six readiness components (resume, technical, communication, assessment,
portfolio, role alignment), each scored only from linked evidence, each
carrying its own confidence and uncertainty. A small-sample safeguard
(`twin-v2`) makes sure one strong interview session can never masquerade
as a confidently-established skill level — evidence-diversity weighting
and prior-weighted shrinkage keep the numbers honest as they did in
practice: a real session that raw-scored 90%/100% on two components
correctly displayed as 60%/75% with an explicit "more evidence needed"
notice once the safeguard shipped.

## CARE

Six real routes (`deterministic`, `single_agent`, `graphrag_agent`,
`multi_agent`, `critic_reflection`, `human_review`), chosen by a pure,
unit-tested policy function from real routing factors — not a fixed
pipeline. Every decision persists a full trace (route, factors, agents
invoked, confidence, cost, latency) in the Trust Center.

## GraphRAG

A real Neo4j-backed concept-dependency graph with a relational fallback
(same content, labeled differently) when Neo4j is unavailable — verified
live by stopping and restarting the Neo4j container mid-session.

## The autonomous loop

Observe → Diagnose → Plan → Teach → Assess → Reflect → Update Twin → Next
mission. A missed assessment question triggers a real CARE-routed
root-cause analysis, produces a mission with concrete tasks and a
recommended resource, and closes the loop when the student answers a
follow-up question — the Career Twin updates with an explanation naming
the exact evidence that changed.

## Interview Arena

Six interview modes, voice or typed answers (never blocked by a denied
microphone), five specialist evaluation agents, CARE deciding which subset
actually runs per answer, and a resume-claim evidence checker that uses
respectful, non-accusatory classifications — never a lie-detection claim.

## Career Experiment Lab

A deterministic, versioned (`sim-v1`) simulation engine: current Career
Twin, evidence quantity/quality/diversity, the concept-dependency graph, a
job description's stated requirements, and the student's own historical
Twin trend all feed a real formula with diminishing returns, headroom
scaling, and uncertainty. An LLM may restate the numbers in prose; it
never computes them. Every result carries the required disclaimer.

## Research evidence

A live Research Benchmark Lab, not a claimed one: CARE-adaptive routing
vs. fixed single-agent vs. fixed multi-agent, agreement rates computed
from a real run; GraphRAG structured traversal vs. vector-only retrieval,
honestly labeled (graph accuracy is 100% by construction, vector-only is a
real, sometimes-lower, measurement); a calibration module computing Brier
score and Expected Calibration Error from real stored evaluation results,
labeled `preliminary` below 30 samples.

## Explainability and trust

The Trust Center shows, for every decision: route, routing factors, every
agent invoked with its confidence and evidence citations, agreement,
policy/formula/prompt versions, cost, and latency — never private
chain-of-thought, always a stored, auditable summary. The Responsible AI
Center states plainly what the system evaluates, what it never will (no
hiring probability, no lie detection, no public ranking, no psychological
inference), and gives every student real self-service data export, audio
deletion, and full account deletion.

## Real-world value

For students: one system that remembers them, explains itself, and turns
"I got this wrong" into a concrete, evidence-backed next step. For
faculty: privacy-safe cohort skill gaps and a list of who actually needs
outreach, not a black-box score. For placement cells: readiness
distribution and program effectiveness, without a fabricated hiring
prediction. For recruiters: only what a student explicitly chooses to
share, evidence and confidence attached, never an automated hiring call.
